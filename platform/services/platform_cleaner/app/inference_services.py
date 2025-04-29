"""Module for removing old inferenceservice instances"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime

from kubernetes_asyncio import client
from kubernetes_asyncio.client.api_client import ApiClient

from configuration import INFERENCE_SERVICE_AGE_THRESHOLD_HOURS
from geti_logger_tools.logger_config import initialize_logger

logger = initialize_logger(__name__)


def get_utc_now() -> datetime.datetime:
    """
    Get current date in UTC timezone.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def is_inference_service_older_than_threshold(inference_service_metadata: dict, max_age_hours: int) -> bool:
    """
    Return True if given InferenceService is older than max_age_hours, return False otherwise.
    """
    creation_timestamp = inference_service_metadata.get("creationTimestamp")
    if not creation_timestamp:
        logger.error(f"Failed to get creationTimestamp for {inference_service_metadata['name']}")
        return False
    parsed_creation_timestamp = datetime.datetime.fromisoformat(creation_timestamp.replace("Z", "")).replace(
        tzinfo=datetime.timezone.utc
    )
    current_date = get_utc_now()

    logger.debug(f"{current_date=}")
    logger.debug(f"{parsed_creation_timestamp=}")

    return (current_date - parsed_creation_timestamp).total_seconds() >= max_age_hours * 60 * 60


async def cleanup_inference_services_older_than_threshold(
    namespace: str, max_age_hours: int = INFERENCE_SERVICE_AGE_THRESHOLD_HOURS
) -> None:
    """
    Remove Inference Services older than max_age_hours in given namespace.
    """
    async with ApiClient() as api:
        custom_objects_api = client.CustomObjectsApi(api)
        inference_services = await custom_objects_api.list_namespaced_custom_object(
            group="serving.kserve.io", version="v1beta1", plural="inferenceservices", namespace=namespace
        )
        for inference_service in inference_services["items"]:
            inference_service_metadata = inference_service.get("metadata", {})
            if is_inference_service_older_than_threshold(inference_service_metadata, max_age_hours):
                logger.info(
                    f"Removing InferenceService {inference_service_metadata['name']}"
                    f" (created {inference_service_metadata.get('creationTimestamp')}),"
                    f" as it is older than {max_age_hours} hours."
                )
                await custom_objects_api.delete_namespaced_custom_object(
                    group="serving.kserve.io",
                    version="v1beta1",
                    plural="inferenceservices",
                    namespace=namespace,
                    name=inference_service_metadata["name"],
                )
