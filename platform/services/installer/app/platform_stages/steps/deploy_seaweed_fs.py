# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import logging
import os
import time

from kubernetes.client import ApiClient, ApiException, CoreV1Api
from kubernetes.stream import stream

from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.charts import SEAWEED_FS_CHART
from constants.paths import K3S_KUBECONFIG_PATH, PLATFORM_INSTALL_PATH
from platform_configuration.features import FeatureFlag, is_feature_flag_enabled
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import (
    ChartInstallationError,
    ChartPullError,
    SeaweedFSBucketTTLError,
    SeaweedFSInstallationError,
)
from platform_utils.helm import pull_chart, save_jinja_template, upsert_chart
from platform_utils.kube_config_handler import KubernetesConfigHandler

logger = logging.getLogger(__name__)
FULL_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, SEAWEED_FS_CHART.values_file))
SEAWEED_FS_POD_NAME = "impt-seaweed-fs-0"
DEFAULT_WEIGHTS_URL = "https://storage.geti.intel.com/weights"

buckets_to_set_ttl = {
    "codedeployments": "1d",
    "resultmedia": "1d",
    "temporaryfiles": "1d",
    "tensors": "1d",
    "mlflowexperiments": "7d",
}


def deploy_seaweed_fs_chart(
    config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH
) -> None:
    """
    Install seaweed chart
    """

    data = {
        "registry": config.image_registry.value,
        "geti_registry": config.geti_image_registry.value,
        "product_build": get_target_product_build(),
        "ff_ambient_mesh": is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH),
        "weights_url": os.getenv("WEIGHTS_URL", DEFAULT_WEIGHTS_URL),
    }
    proxy_http = os.getenv("http_proxy") or os.getenv("HTTP_PROXY")
    proxy_https = os.getenv("https_proxy") or os.getenv("HTTPS_PROXY")
    proxy_no_proxy = os.getenv("no_proxy") or os.getenv("NO_PROXY")
    data["proxy_enabled"] = bool(proxy_http or proxy_https)
    data["proxy_http"] = proxy_http
    data["proxy_https"] = proxy_https
    data["proxy_no_proxy"] = proxy_no_proxy

    save_jinja_template(SEAWEED_FS_CHART.values_template_file, data, FULL_VALUES_FILE_NAME)

    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None
        chart_dir = str(os.path.join(charts_dir, SEAWEED_FS_CHART.directory))
        if chart_version:
            pull_chart(chart_version, chart_dir)
        upsert_chart(
            name=SEAWEED_FS_CHART.name,
            version=chart_version,
            chart_dir=chart_dir,
            namespace=SEAWEED_FS_CHART.namespace,
            values=[FULL_VALUES_FILE_NAME],
            timeout="60m",
            wait_for_jobs=False,
        )
    except (ChartInstallationError, ChartPullError) as ex:
        raise SeaweedFSInstallationError from ex

    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)

    with ApiClient() as api_client:
        core_api = CoreV1Api(api_client)
        try:
            set_bucket_ttl(core_api)
        except Exception as ex:
            raise SeaweedFSInstallationError from ex


def set_bucket_ttl(core_api: CoreV1Api, retries: int = 10) -> None:
    """
    Set TTL for SeaweedFS buckets with retry logic and exponential backoff.
    """
    for bucket, ttl in buckets_to_set_ttl.items():
        command = [
            "/bin/sh",
            "-c",
            f'echo "fs.configure -locationPrefix=/buckets/{bucket}/ -ttl={ttl} -apply" | weed shell',
        ]
        for attempt in range(retries):
            try:
                resp = core_api.read_namespaced_pod(name=SEAWEED_FS_POD_NAME, namespace=SEAWEED_FS_CHART.namespace)
                if resp.status.phase != "Running":
                    raise RuntimeError(f"Pod {SEAWEED_FS_POD_NAME} is not running (current status:{resp.status.phase})")
                stream(
                    core_api.connect_get_namespaced_pod_exec,
                    name=SEAWEED_FS_POD_NAME,
                    namespace=SEAWEED_FS_CHART.namespace,
                    command=command,
                    container="main",
                    stderr=True,
                    stdin=False,
                    stdout=True,
                    tty=False,
                )
                logger.info(f"Successfully set TTL for bucket '{bucket}'")
                break
            except ApiException as ex:
                logger.warning(f"Attempt {attempt}/{retries} failed for bucket '{bucket}': {ex}")
                if attempt == retries:
                    raise SeaweedFSBucketTTLError(f"Failed to set TTL for bucket '{bucket}' after {retries} attempts")
                time.sleep(1)
