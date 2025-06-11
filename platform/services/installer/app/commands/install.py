# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
CLI command for install operation.
"""

import logging
import os
import shutil
import signal
import sys
from functools import partial
from typing import TYPE_CHECKING

import rich_click as click

from checks.dns import check_dns_ipv4_handling
from checks.errors import CumulativeCheckError
from checks.internet import check_internet_connection
from checks.k8s import (
    check_k8s_is_not_installed,
)
from checks.os import check_os_version
from checks.ports import check_required_ports_availability
from checks.resources import (
    check_gpu_driver_version,
    check_local_cpu,
    check_local_disk,
    check_local_gpu,
    check_local_mem,
)
from checks.user import check_user_id
from cli_utils.checks import run_checks

# from platform_configuration.versions import get_target_product_build
from cli_utils.credentials import hash_ldap_password
from cli_utils.platform_logs import configure_logging, create_logs_dir
from cli_utils.spinner import click_spinner
from configuration_models.install_config import InstallationConfig
from constants.paths import (
    K3S_INSTALLATION_MARK_FILEPATH,
    K3S_KUBECONFIG_PATH,
    OFFLINE_TOOLS_DIR,
)

# from platform_configuration.versions import get_target_product_build
from constants.platform import DEFAULT_USERNAME
from geti_controller.communication import call_install_endpoint
from geti_controller.install import deploy_geti_controller_chart
from geti_controller.uninstall import uninstall_geti_controller_chart
from k3s.detect_ip import get_first_public_ip, get_master_node_ip_address
from k3s.install import K3SInstallationError, install_k3s
from k3s.uninstall import uninstall_k3s
from platform_stages.install import install_platform
from platform_stages.steps.errors import DownloadSystemPackagesError, StepsError
from platform_stages.steps.install_system_packages import install_system_packages
from platform_utils.management.state import InstallationHandlerState, cluster_info_dump
from texts.checks import (
    DNSChecksTexts,
    InternetConnectionChecksTexts,
    K8SChecksTexts,
    LocalOSChecksTexts,
    LocalUserChecksTexts,
    PortsAvailabilityCheckTexts,
    ResourcesChecksTexts,
)
from texts.install_command import InstallCmdConfirmationTexts, InstallCmdTexts
from validators.email import is_email_valid
from validators.filepath import is_filepath_valid
from validators.password import is_password_valid
from validators.path import is_data_folder_valid
from validators.tls import check_tls_certificates

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


def custom_interrupt_handler_with_args(handler_state: InstallationHandlerState, data_folder: str):  # noqa: ANN201
    """
    Handle installation interruption
    """

    def handler(sig, frame):  # noqa: ARG001, ANN001
        if not handler_state.trigger():
            return

        if handler_state.can_be_aborted:
            logger.warning("Installation of the platform was aborted.")
            click.secho("\n" + InstallCmdTexts.installation_aborted, fg="yellow")
            with click_spinner.spinner():
                uninstall_k3s(delete_data=True, data_folder=data_folder)
            click.secho("\n" + InstallCmdTexts.installation_aborted_succeeded, fg="green")
            sys.exit(0)
        else:
            logger.warning("k3s installation cannot be aborted")
            click.secho("\n" + InstallCmdTexts.k3s_installation_in_progress, fg="yellow")
            handler_state.clear_trigger()

    return handler


def set_custom_signal_handler(handler_state: InstallationHandlerState, data_folder: str) -> None:
    """
    Set custom signal handler for installation.
    """
    handler = custom_interrupt_handler_with_args(handler_state, data_folder)
    signal.signal(signal.SIGINT, handler)


def initial_checks(config: InstallationConfig) -> None:
    """
    Run initial checks, executed before install wizard prompts.
    """
    checks: list[tuple[str, Callable]] = [
        (LocalUserChecksTexts.user_check_start, check_user_id),
        (LocalOSChecksTexts.os_check_start, partial(check_os_version, config=config)),
        (
            InternetConnectionChecksTexts.internet_connection_check_start,
            partial(check_internet_connection, config=config),
        ),
        (DNSChecksTexts.dns_ipv4_config_check, partial(check_dns_ipv4_handling, config=config)),
    ]

    run_checks(checks=checks)


def install_checks(config: InstallationConfig) -> None:
    """
    Run pre-installation checks.
    """
    checks: list[tuple[str, Callable]]
    checks = [
        (ResourcesChecksTexts.resources_check_cpu, check_local_cpu),
        (ResourcesChecksTexts.resources_check_mem, check_local_mem),
        (ResourcesChecksTexts.resources_check_disk, check_local_disk),
        (
            ResourcesChecksTexts.gpu_requirements_check_start,
            partial(check_local_gpu, config=config),
        ),
        (
            ResourcesChecksTexts.gpu_driver_version_check_start,
            partial(check_gpu_driver_version, config=config),
        ),
        (K8SChecksTexts.already_installed_k8s_check_start, check_k8s_is_not_installed),
        (PortsAvailabilityCheckTexts.ports_availability_check_start, check_required_ports_availability),
    ]

    run_checks(checks=checks)


def run_initial_checks(config: InstallationConfig) -> None:
    """
    Run initial_checks, print a message and terminate script execution on error.
    """
    try:
        initial_checks(config=config)
    except CumulativeCheckError:
        click.echo(InstallCmdTexts.checks_error_message)
        sys.exit(1)


def run_installation_checks(config: InstallationConfig) -> None:
    """
    Run install_checks, print a message and terminate script execution on error.
    """
    try:
        install_checks(config=config)
    except CumulativeCheckError:
        click.echo(InstallCmdTexts.checks_error_message)
        sys.exit(1)


def execute_installation(config: InstallationConfig) -> None:  # noqa: C901, RUF100
    """
    Execute platform installation with passed configuration.
    """
    click.echo(InstallCmdTexts.execution_start_message)

    handler_state = InstallationHandlerState()
    set_custom_signal_handler(handler_state, config.data_folder.value)

    try:
        click.echo(InstallCmdTexts.sys_pkgs_installing)
        install_system_packages(config)
        click.secho(InstallCmdTexts.sys_pkgs_installation_succeeded, fg="green")
    except DownloadSystemPackagesError:
        logger.exception("Error during system packages installation.")
        click.secho(InstallCmdTexts.sys_pkgs_installation_failed, fg="red")
        sys.exit(1)

    config.kube_config.value = K3S_KUBECONFIG_PATH

    click.echo(InstallCmdTexts.k3s_installing)
    logger.info(InstallCmdTexts.k3s_installing)
    try:
        with click_spinner.spinner():
            install_k3s()
    except K3SInstallationError:
        logger.exception("Error during k3s installation.")
        click.secho(InstallCmdTexts.k3s_installation_failed, fg="red")
        if config.lightweight_installer.value:
            # remove 'tools' dir on failure,
            # to be able to re-run without any side effects
            shutil.rmtree(OFFLINE_TOOLS_DIR)
        sys.exit(1)
    click.secho(InstallCmdTexts.k3s_installation_succeeded, fg="green")
    logger.info(InstallCmdTexts.k3s_installation_succeeded)

    handler_state.reset()

    if os.path.exists(K3S_INSTALLATION_MARK_FILEPATH):
        config.master_ip_autodetected.value = get_first_public_ip()

    try:
        deploy_geti_controller_chart(config=config)
        controller_response = call_install_endpoint(kube_config=config.kube_config.value)
        logger.info(f"Response from the GetiController installation endpoint: {controller_response}")
    except StepsError:
        logger.exception("Error during installation.")
        click.secho("\n" + InstallCmdTexts.installation_failed, fg="red")
        cluster_info_dump(kubeconfig=config.kube_config.value)
        sys.exit(1)
    finally:
        # uninstall_geti_controller_chart(config=config)
        # shutil.rmtree(PLATFORM_INSTALL_PATH, ignore_errors=True)  # TODO uncomment
        if config.lightweight_installer.value:
            # remove 'tools' dir on failure,
            # to be able to re-run without any side effects
            shutil.rmtree(OFFLINE_TOOLS_DIR)

    if config.master_ip_autodetected.value:
        platform_address = config.master_ip_autodetected.value
    else:
        platform_address = get_master_node_ip_address(kubeconfig_path=config.kube_config.value)

    click.secho("\n" + InstallCmdTexts.installation_succeeded.format(platform_address=platform_address), fg="green")


def display_final_confirmation(config: InstallationConfig) -> None:
    """
    Display the gathered data and asks for the confirmation.
    """
    click.echo()
    click.echo(InstallCmdConfirmationTexts.confirm_username_message.format(username=config.username.value))
    click.secho(InstallCmdTexts.selected_password, nl=False)
    click.secho(config.password.value, fg="yellow")
    click.echo()

    if config.custom_certificate:
        click.echo(InstallCmdConfirmationTexts.cert_file_message.format(path=config.tls_cert_file.value))
        click.echo(InstallCmdConfirmationTexts.key_file_message.format(path=config.tls_key_file.value))
    else:
        click.echo(InstallCmdConfirmationTexts.no_custom_certificate_message)

    click.echo()
    click.echo(InstallCmdConfirmationTexts.confirm_data_message.format(path=config.data_folder.value))


@click.command()
@click.option(  # TODO remove later, workaround for Jenkins builds
    "--config-file",
    type=click.Path(exists=True, resolve_path=True, dir_okay=False),
    required=False,
    help="Config file with installation parameters. When calling installer outside of its directory use absolute path.",
)
@click.option(
    "--data-folder",
    type=click.Path(),
    callback=is_data_folder_valid,
    help="Absolute path to directory where Geti data will be stored.",
)
@click.option(
    "--username",
    default=DEFAULT_USERNAME,
    callback=is_email_valid,
    help=InstallCmdTexts.username_help,
)
@click.option("--password", callback=is_password_valid, help=InstallCmdTexts.password_help)
@click.option("--tls-cert-file", type=click.Path(), callback=is_filepath_valid, help=InstallCmdTexts.tls_cert_file_help)
@click.option("--tls-key-file", type=click.Path(), callback=is_filepath_valid, help=InstallCmdTexts.tls_key_file_help)
def install(
    data_folder: str | None,
    username: str,
    password: str,
    tls_cert_file: str | None = None,
    tls_key_file: str | None = None,
    config_file: str | None = None,  # TODO remove later, workaround for Jenkins builds
) -> None:
    """
    Install platform.
    """
    logger.debug(f"Remove {config_file} param later")  # TODO
    click.echo(InstallCmdTexts.start_message)
    create_logs_dir()
    configure_logging()
    config = InstallationConfig()
    config.data_folder.value = data_folder
    config.username.value = username
    config.password.value = password
    config.password_sha.value = hash_ldap_password(config.password.value)
    check_tls_certificates(tls_cert_file=tls_cert_file, tls_key_file=tls_key_file)
    config.tls_key_file.value = tls_key_file
    config.tls_cert_file.value = tls_cert_file
    run_initial_checks(config=config)
    run_installation_checks(config=config)
    display_final_confirmation(config=config)
    execute_installation(config=config)
