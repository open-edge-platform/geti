# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
A module responsible for Helm Chart upgrade/installation.
"""

import logging
import os.path
import shutil
import subprocess

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from cli_utils.platform_logs import subprocess_run
from constants.paths import HELM_BINARY, INSTALL_LOG_FILE_PATH, K3S_KUBECONFIG_PATH, TEMPLATES_DIR
from constants.platform import PLATFORM_REGISTRY_ADDRESS
from platform_stages.steps.errors import ChartInstallationError, ChartPullError, GenerateTemplateError
from platform_utils.k8s import ensure_endpoint

logger = logging.getLogger(__name__)

STOP_AFTER_ATTEMPT = 1
WAIT_FIXED = 30


def pull_chart(version: str, chart_dir: str) -> None:
    """
    Function that will pull the chart and unpack it.
    """
    name = os.path.basename(chart_dir)
    destination = os.path.dirname(chart_dir)
    os.makedirs(destination, exist_ok=True)

    logger.info(f"Pulling chart '{name}', version '{version}', to '{destination}'")
    command = [
        HELM_BINARY,
        "pull",
        f"--destination={destination}",
        f"oci://{PLATFORM_REGISTRY_ADDRESS}/open-edge-platform/geti/helm/{name}",
        f"--version={version}",
    ]

    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        try:
            subprocess_run(command, log_file)
        except subprocess.CalledProcessError as ex:
            raise ChartPullError from ex

    untar_command = ["tar", "-zxf", f"{destination}/{name}-{version}.tgz", "-C", destination]

    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        try:
            subprocess_run(untar_command, log_file)
        except subprocess.CalledProcessError as ex:
            raise ChartPullError from ex

    shutil.rmtree(f"{destination}/{name}-{version}.tgz", ignore_errors=True)


@ensure_endpoint()
@retry(
    retry=retry_if_exception_type(ChartInstallationError),
    stop=stop_after_attempt(STOP_AFTER_ATTEMPT),
    wait=wait_fixed(WAIT_FIXED),
    reraise=True,
)
def upsert_chart(  # noqa: PLR0913
    name: str,
    chart_dir: str,
    namespace: str = "default",
    version: str | None = None,
    values: list[str] | None = None,
    timeout: str = "10m",
    sets: str | None = None,
    wait_for_jobs: bool = True,
) -> None:
    """
    Function that will install chart or upgrade if chart already exists.
    It will raise an exception if it fails.

    Note:
        'sets' param can be used to define multiple values i.e.: key1=val1,key2=val2
        Order of files in 'values' param is important.
    """
    logger.info(f"Installing chart '{name}' from '{chart_dir}'.")
    command = [
        HELM_BINARY,
        "upgrade",
        "-i",
        name,
        f"--namespace={namespace}",
        chart_dir,
        "--wait=true",
        f"--timeout={timeout}",
        "--force",
        f"--kubeconfig={K3S_KUBECONFIG_PATH}",
    ]
    if wait_for_jobs:
        command.extend(["--wait-for-jobs"])
    if version:
        command.extend([f"--version={version}"])
    if values:
        command.extend([f"--values={value}" for value in values])
    if sets:
        command.append(f"--set={sets}")
    logger.debug(f"Invoked following command: \n./{' '.join(command)}")

    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        try:
            subprocess_run(command, log_file)
        except subprocess.CalledProcessError as ex:
            raise ChartInstallationError from ex


def save_jinja_template(source_file: str, data: dict, destination_file: str) -> None:
    """
    Method used to render templates and save file in destination.
    """
    logger.info("Generating Jinja template.")
    try:
        environment = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
        template = environment.get_template(source_file)
        content = template.render(data)
        logger.debug(f"Template: {content}")
        with open(destination_file, "w", encoding="utf-8") as jinja_file:
            jinja_file.write(content)
    except TemplateError as ex:
        raise GenerateTemplateError from ex
    logger.info("Generation of Jinja template succeeded.")
