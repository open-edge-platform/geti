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
import os

import yaml

from configuration_models.install_config import InstallationConfig
from constants.charts import ISTIO_GATEWAY_CHART
from constants.paths import PLATFORM_INSTALL_PATH
from platform_configuration.features import FeatureFlag, get_updated_feature_flags, is_feature_flag_enabled
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import ChartInstallationError, ChartPullError, IstioGatewayInstallationError
from platform_utils.helm import pull_chart, save_jinja_template, upsert_chart
from platform_utils.k8s import encode_data_b64

FULL_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, ISTIO_GATEWAY_CHART.values_file))


def deploy_istio_gateway_chart(config: InstallationConfig, charts_dir: str = PLATFORM_INSTALL_PATH) -> None:
    """
    Method used to deploy istio gateway chart
    """
    data = {
        "registry": config.image_registry.value,
        "geti_registry": config.geti_image_registry.value,
        "product_build": get_target_product_build(),
        "feature_flags_data": yaml.safe_dump(get_updated_feature_flags()),
        "ff_ambient_mesh": is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH),
    }

    if (
        isinstance(config, InstallationConfig)
        and config.tls_cert_file
        and config.tls_key_file
        and config.tls_cert_file.value
        and config.tls_key_file.value
    ):
        with open(config.tls_cert_file.value, "rb") as tls_cert_file:
            cert_content = tls_cert_file.read()
            data["tls_cert_file"] = encode_data_b64(cert_content)

        with open(config.tls_key_file.value, "rb") as tls_key_file:
            key_content = tls_key_file.read()
            data["tls_key_file"] = encode_data_b64(key_content)

    save_jinja_template(
        source_file=ISTIO_GATEWAY_CHART.values_template_file, data=data, destination_file=FULL_VALUES_FILE_NAME
    )
    values_file = [FULL_VALUES_FILE_NAME]
    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None
        chart_dir = str(os.path.join(charts_dir, ISTIO_GATEWAY_CHART.directory))
        if chart_version:
            pull_chart(chart_version, chart_dir)
        upsert_chart(
            name=ISTIO_GATEWAY_CHART.name,
            version=chart_version,
            chart_dir=chart_dir,
            namespace=ISTIO_GATEWAY_CHART.namespace,
            values=values_file,
        )
    except (ChartInstallationError, ChartPullError) as ex:
        raise IstioGatewayInstallationError from ex
