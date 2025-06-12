# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import asyncio
import logging
import os
import re

import jinja2
import yaml
from fastapi import APIRouter, FastAPI
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

platform_router = APIRouter(prefix="/platform", tags=["Platform"])


class JobManager:
    def __init__(self):
        self.status = "RUNNING"
        self.message = ""
        self.progress = 0

    def get_status(self) -> dict[str, str | int]:
        return {"status": self.status, "message": self.message, "progress": self.progress}

    def set_status(self, status: str, message: str = "", progress: float | None = None) -> None:
        self.status = status
        self.message = message
        if progress is not None:
            self.progress = progress


job_manager = JobManager()


@platform_router.get("/progress")
async def get_job_status() -> dict[str, str | int]:
    """
    Get progress of job process
    """
    return job_manager.get_status()


async def download_manifest() -> str:
    """
    Download the GETI manifest file from the OCI registry.
    Returns the path to the downloaded manifest file.
    """
    logger.info("Downloading GETI manifest from the OCI registry...")
    oc = OrasClient(tls_verify=False)
    res = await asyncio.to_thread(
        oc.pull, target=f"{GETI_REGISTRY}/geti/geti-manifest:{GETI_MANIFEST_VERSION}", outdir="."
    )
    logger.info("Geti manifest downloaded successfully.")
    logger.debug(f"Downloaded manifest file: {res[0]}")
    return res[0]


async def load_and_split_file(path: str) -> list[str]:
    """
    Load file specified by path and split it into sections based on '---'.
    Removes the first section which is geti metadata.
    Returns a list of sections.
    """
    logger.info(f"Loading file {path}...")

    def read_file() -> str:
        with open(path) as file:
            return file.read()

    content = await asyncio.to_thread(read_file)
    file_sections = content.split("---")
    file_sections.pop(0)  # Remove the first section

    logger.info(f"Following {len(file_sections)} sections found.")
    return file_sections


async def render_jinja_template(template_string: str) -> dict:
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


async def deploy_helm_charts(manifest: dict) -> None:
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
            await asyncio.to_thread(
                custom_api.create_namespaced_custom_object,
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


async def wait_for_job_completion(job_name: str, namespace: str, timeout: int = 300) -> None:
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
        events = await asyncio.to_thread(
            lambda: list(w.stream(batch_v1.list_namespaced_job, namespace=namespace, timeout_seconds=timeout))
        )
        for event in events:
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


async def main(job_manager: JobManager) -> None:
    """
    Main function that orchestrates the installation/upgrade process.
    It will be done in a couple of steps:
    1. Download the manifest file from the oci registry.
    2. Parse the manifest file to get the helm charts CR's.
    3. For each CR render the jinja template with the required variables.
    4. Deploy the rendered helm charts to the Kubernetes cluster.
    5. Wait for the helm install job to complete.
    """
    job_manager.set_status("RUNNING", progress=0)
    logger.info("Installation process started.")
    config.load_config()
    logger.info("Initialized Kubernetes client configuration...")
    try:
        geti_manifest = await download_manifest()
        helm_charts = await load_and_split_file(geti_manifest)
        total_charts = len(helm_charts)
        for index, helm in enumerate(helm_charts):
            rendered_helm = await render_jinja_template(helm)
            try:
                job_manager.set_status("RUNNING", message=f"Deploying helm chart {rendered_helm['metadata']['name']}")
                await deploy_helm_charts(rendered_helm)
            except HelmChartDeployError as e:
                logger.error(f"Failed to deploy helm chart: {e}")
                job_manager.set_status("FAILED", str(e), progress=(index / total_charts) * 100)
                break

            job_name = f"helm-install-{rendered_helm['metadata']['name']}"
            namespace = rendered_helm["metadata"]["namespace"]
            parsed_timeout = (
                parse_timeout(rendered_helm["spec"]["timeout"]) if "timeout" in rendered_helm["spec"] else None
            )
            try:
                await wait_for_job_completion(
                    job_name=job_name, namespace=namespace, timeout=parsed_timeout if parsed_timeout else 300
                )
            except (FailedJobError, TimeoutJobError) as e:
                logger.error(f"Job '{job_name}' in namespace '{namespace}' failed: {e}")
                job_manager.set_status("FAILED", str(e), progress=(index / total_charts) * 100)
                break
            except UnknownJobError as e:
                logger.exception(f"Unexpected error while completing job '{job_name}' in namespace '{namespace}': {e}")
                job_manager.set_status("FAILED", str(e), progress=(index / total_charts) * 100)
                break

            job_manager.set_status(
                "RUNNING", progress=((index + 1) / total_charts) * 100, message=f"helm chart {job_name} installed"
            )

            await asyncio.sleep(0)

        else:
            job_manager.set_status("SUCCEEDED", progress=100, message="Installation process completed successfully.")
            logger.info("Installation process completed successfully.")
    except Exception as e:
        job_manager.set_status("FAILED", str(e))
        logger.error(f"Installation process failed: {e}")


async def run() -> None:
    """
    Gather function for FastAPI server and installer job
    """
    import uvicorn

    app = FastAPI()
    app.include_router(platform_router, prefix="/api/v1")
    server_started_event = asyncio.Event()

    @app.on_event("startup")
    async def on_startup():
        server_started_event.set()

    server = uvicorn.Server(uvicorn.Config(app, host="localhost", port=8000))
    server_task = asyncio.create_task(server.serve())
    await server_started_event.wait()
    await main(job_manager)
    await asyncio.sleep(300)

    server_task.cancel()


if __name__ == "__main__":
    asyncio.run(run())
