"""Module for platform's workloads auto removal"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import asyncio

from kubernetes_asyncio import config

from geti_logger_tools.logger_config import initialize_logger
from inference_services import cleanup_inference_services_older_than_threshold
from telemetry import cleanup_telemetry_samples

config.load_incluster_config()

logger = initialize_logger(__name__)


async def run_platform_cleaner():  # noqa: ANN201
    """
    platform's workloads removal main function
    """
    tasks = []

    tasks.append(asyncio.create_task(cleanup_telemetry_samples()))
    # Cleanup inference services for on-prem
    tasks.append(asyncio.create_task(cleanup_inference_services_older_than_threshold(namespace="impt")))
    # Cleanup inferennce services for SaaS
    tasks.append(asyncio.create_task(cleanup_inference_services_older_than_threshold(namespace="modelmesh")))

    await asyncio.gather(*tasks)


def main():  # noqa: ANN201
    """
    platform's workloads removal main function
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_platform_cleaner())
    loop.close()


if __name__ == "__main__":
    main()
