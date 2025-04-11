# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import asyncio
import logging
import sys

from service.inference_service import InferenceService

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


class InferenceManager:
    async def create_inference(self, name: str, namespace: str, storage_name: str, path: str) -> None:
        """Create inferenceservice resource"""
        logging.info(f"Creating InferenceService for {name}")
        inference = InferenceService(name=name, namespace=namespace, storage_name=storage_name, path=path)
        await inference.create()
        create_timeout = 300
        for _ in range(create_timeout):
            await asyncio.sleep(0.1)
            inference_service: InferenceService | None = await InferenceService.get(name=name, namespace=namespace)  # type: ignore
            if inference_service and inference_service.status and "conditions" in inference_service.status:
                for condition in inference_service.status["conditions"]:
                    if condition.get("type") == "Ready" and condition.get("status") == "True":
                        break
                else:
                    continue
                break
        else:
            raise RuntimeError(f"Failed to create {name} InferenceService")
        logging.info(f"Created InferenceService for {name}")

    async def remove_inference(self, name: str, namespace: str) -> None:
        """Deletes specific inferenceservice resource."""
        logging.info(f"Removing InferenceService for {name}")
        deletion_timeout = 600

        inference_service: InferenceService | None = await InferenceService.get(name=name, namespace=namespace)  # type: ignore

        if inference_service:
            await inference_service.delete(propagation_policy="Foreground")
            for _ in range(deletion_timeout):
                inference_service: InferenceService | None = await InferenceService.get(name=name, namespace=namespace)  # type: ignore
                if not inference_service:
                    break
                await asyncio.sleep(0.1)
            else:
                raise RuntimeError(f"Failed to remove {name} InferenceService")
            logger.info(f"Removed {name} InferenceService")
        else:
            raise RuntimeError(f"InferenceService {name} not found")

    async def list_inference(self, namespace: str) -> list[InferenceService]:
        """List registered inferenceservice resources."""
        logging.info(f"Listing items in InferenceService within namespace `{namespace}`")
        return await InferenceService.list(namespace=namespace)  # type: ignore

    async def get_inference(self, name: str, namespace: str) -> InferenceService | None:
        """Get specific inferenceservice resource."""
        logging.info(f"Getting InferenceService for {name}")
        inference_service: InferenceService | None = await InferenceService.get(name=name, namespace=namespace)  # type: ignore
        return inference_service
