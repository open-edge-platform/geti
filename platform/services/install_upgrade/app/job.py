# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os
import re
import sys

import jinja2
import yaml
from kubernetes import client, config, watch
from oras.client import OrasClient

from error import FailedJobError, HelmChartDeployError, ParseDurationError, TimeoutJobError, UnknownJobError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


GETI_REGISTRY = os.getenv("GETI_REGISTRY", "")
GETI_MANIFEST_VERSION = os.getenv("GETI_MANIFEST_VERSION", "")
DATA_FOLDER = os.getenv("DATA_FOLDER", "")
USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")
TLS_CERT = os.getenv("TLS_CERT", "")
TLS_KEY = os.getenv("TLS_KEY", "")


def download_manifest() -> str:
    """
    Download the GETI manifest file from the OCI registry.
    Returns the path to the downloaded manifest file.
    """

    logger.info("Downloading GETI manifest from the OCI registry...")
    oc = OrasClient(tls_verify=False)

    res = oc.pull(target=f"{GETI_REGISTRY}/geti/geti-manifest:{GETI_MANIFEST_VERSION}", outdir=".")
    logger.info("Geti manifest downloaded successfully.")
    logger.debug(f"Downloaded manifest file: {res[0]}")
    return res[0]


def load_and_split_file(path: str) -> list[str]:
    """
    Load file specified by path and split it into sections based on '---'.
    Removes the first section which is geti metadata.
    Returns a list of sections.
    """
    logger.info(f"Loading file {path}...")
    with open(path) as file:
        content = file.read()

    file_sections = content.split("---")
    file_sections.pop(0)  # Remove the first section

    logger.info(f"Following {len(file_sections)} sections found.")
    return file_sections


def render_jinja_template(template_string: str) -> dict:
    """
    Render the Jinja template with the required variables.
    Return the rendered template as a dictionary.
    """
    logger.info("Rendering Jinja template...")
    template = jinja2.Template(template_string)

    # Define the variable
    data = {
        "data_folder": DATA_FOLDER,
        "username": USERNAME,
        "password": PASSWORD,
        "tls_cert_file": TLS_CERT,
        "tls_key_file": TLS_KEY,
    }

    # Render the template with the variable
    rendered_output = template.render(data)
    logger.debug(f"Rendered Jinja template: {rendered_output}")

    logger.info("Rendered template successfully.")
    return yaml.safe_load(rendered_output)


def deploy_helm_charts(manifest: dict) -> None:
    """
    Deploy the rendered helm chart to the Kubernetes cluster.
    In case of conflict (e.g., chart already exists), it will log an error.
    """
    logger.info(
        f"Deploying helm chart CR: '{manifest['metadata']['name']}' in namespace '{manifest['metadata']['namespace']}'."
    )

    with client.ApiClient() as api_client:
        custom_api = client.CustomObjectsApi(api_client)
        try:
            custom_api.create_namespaced_custom_object(
                namespace=manifest["metadata"]["namespace"],
                group="helm.cattle.io",
                plural="helmcharts",
                version="v1",
                body=manifest,
            )
        except client.exceptions.ApiException as e:
            if e.status == 409:
                logger.exception("CR already exists.")
                raise HelmChartDeployError("Helm chart CR already exists. Please check the logs for more details.")
    logger.info("Deployed helm charts successfully.")


def wait_for_job_completion(job_name: str, namespace: str, timeout: int = 300) -> None:
    """
    Wait for a Kubernetes job to complete using the Python API.
    When job will fail or there will be timeout script will break and raise an exception.

    :param job_name: name of job to wait for.
    :param namespace: namespace where the job is located.
    :param timeout: Maximum time to wait in seconds.
    """
    batch_v1 = client.BatchV1Api()
    w = watch.Watch()

    logger.info(f"Waiting for job '{job_name}' to complete in namespace '{namespace}'...")
    try:
        for event in w.stream(batch_v1.list_namespaced_job, namespace=namespace, timeout_seconds=timeout):
            job = event["object"]
            if job.metadata.name != job_name:
                logger.debug(f"Skipping event for job '{job.metadata.name}', waiting for '{job_name}'...")
                continue

            if job.status.succeeded:
                logger.info(f"Job '{job_name}' completed successfully.")
                return
            if job.status.failed:
                raise FailedJobError(f"Job '{job_name}' failed.")

    except client.ApiException as e:
        logger.exception(f"Error while waiting for job '{job_name}': {e}")
        raise UnknownJobError(f"Unknown job '{job_name}' encountered. Please check the job name and namespace.")
    finally:
        w.stop()
    raise TimeoutJobError(f"Timeout while waiting for job '{job_name}' after {timeout} seconds.")


def parse_timeout(timeout: str) -> int:
    """
    Parse timeout string to seconds.
    :param timeout: Timeout string (e.g., '600s', '10m', '2h').
    :return: Timeout in seconds.
    """
    match = re.match(r"(\d+)([smh]?)", timeout.lower())
    if not match:
        raise ParseDurationError("Invalid timeout format. Use '<number>s', '<number>m', or '<number>h'.")
    value, unit = match.groups()
    value = int(value)
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    return value


def main() -> None:
    """
    Main function that orchestrates the installation/upgrade process.
    It will be done in a couple of steps:
    1. Download the manifest file from the oci registry.
    2. Parse the manifest file to get the helm charts CR's.
    3. For each CR render the jinja template with the required variables.
    4. Deploy the rendered helm charts to the Kubernetes cluster.
    5. Wait for the helm install job to complete.
    """
    logger.info("Installation process started.")
    config.load_config()
    logger.info("Initialized Kubernetes client configuration...")
    geti_manifest = download_manifest()
    helm_charts = load_and_split_file(geti_manifest)
    for helm in helm_charts:
        rendered_helm = render_jinja_template(helm)
        try:
            deploy_helm_charts(rendered_helm)
        except HelmChartDeployError as e:
            logger.error(f"Failed to deploy helm chart: {e}")
            sys.exit(1)

        job_name = f"helm-install-{rendered_helm['metadata']['name']}"
        namespace = rendered_helm["metadata"]["namespace"]
        parsed_timeout = parse_timeout(rendered_helm["spec"]["timeout"]) if "timeout" in rendered_helm["spec"] else None
        try:
            wait_for_job_completion(
                job_name=job_name, namespace=namespace, timeout=parsed_timeout if parsed_timeout else 300
            )
        except (FailedJobError, TimeoutJobError) as e:
            logger.error(f"Job '{job_name}' in namespace '{namespace}' failed: {e}")
            sys.exit(2)
        except UnknownJobError as e:
            logger.exception(f"Unexpected error while completing job '{job_name}' in namespace '{namespace}': {e}")
            sys.exit(3)

    logger.info("Installation process completed successfully.")


if __name__ == "__main__":
    main()
