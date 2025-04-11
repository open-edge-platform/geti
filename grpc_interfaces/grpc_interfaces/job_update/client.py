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

import json
import logging
import os
from collections.abc import Callable
from typing import Any, TypeVar

import grpc
from grpc import Channel, insecure_channel  # type: ignore # grpc types not available in mypy

from .pb.job_update_service_pb2 import JobUpdateRequest, JobUpdateResponse
from .pb.job_update_service_pb2_grpc import JobUpdateServiceStub

logger = logging.getLogger(__name__)
TMethod = TypeVar("TMethod", bound=Callable[..., Any])

# Telemetry is an optional yet recommended dependency for this gRPC client
try:
    from geti_telemetry_tools import ENABLE_TRACING, GrpcClientTelemetry

    if ENABLE_TRACING:
        GrpcClientTelemetry.instrument()
        logger.info("gRPC client instrumented for tracing")
    else:
        logger.info("gRPC client NOT instrumented for tracing (ENABLE_TRACING is false)")
except (ModuleNotFoundError, ImportError):
    logger.warning("gRPC client NOT instrumented for tracing (missing telemetry package)")

GRPC_MAX_MESSAGE_SIZE = int(os.environ.get("GRPC_MAX_MESSAGE_SIZE", 128 * 1024**2))  # noqa: PLW1508


class JobUpdateClient:
    """
    Client to send job updates via gRPC.

    :param grpc_address: Address of the gRPC server.
    :param metadata_getter: Lazy-evaluated function that returns the metadata to include
        in the gRPC request. It is typically used to propagate the session context.
    :raises ValueError: If metadata_getter returns None
    """

    grpc_channel: Channel
    job_update_service_stub: JobUpdateServiceStub
    grpc_channel_config: str = json.dumps(
        {
            "methodConfig": [
                {
                    "name": [{}],
                    "retryPolicy": {
                        "maxAttempts": 5,
                        "initialBackoff": "1s",
                        "maxBackoff": "4s",
                        "backoffMultiplier": 2,
                        "retryableStatusCodes": ["UNAVAILABLE"],
                    },
                }
            ]
        }
    )

    def __init__(self, metadata_getter: Callable[[], tuple[tuple[str, str], ...]]) -> None:
        self.metadata_getter = metadata_getter
        if not self.metadata_getter():
            raise ValueError("Unable to get session from metadata")
        self.grpc_address = os.getenv("JOBS_SCHEDULER", "localhost:50051")
        logger.info("Initializing JobUpdateClient on address `%s`.", self.grpc_address)
        self.grpc_channel = insecure_channel(
            self.grpc_address,
            options=[
                ("grpc.service_config", self.grpc_channel_config),
                ("grpc.max_send_message_length", GRPC_MAX_MESSAGE_SIZE),
                ("grpc.max_receive_message_length", GRPC_MAX_MESSAGE_SIZE),
            ],
        )

        self.job_update_service_stub = JobUpdateServiceStub(self.grpc_channel)

    def job_update(
        self,
        execution_id: str,
        metadata: dict | None = None,
        cost: JobUpdateRequest.Cost | None = None,
        gpu: JobUpdateRequest.Gpu | None = None,
    ) -> None:
        """
        Sends a request to update running job information (metadata, consumed cost, GPU action).

        :param execution_id: job Flyte execution ID
        :param metadata: job's metadata
        :param cost: job consumed costs update
        :param gpu: GPU update
        :raises: ValueError if the metadata is not serializable
        """
        if metadata is None and cost is None and gpu is None:
            return

        try:
            metadata_serial = json.dumps(metadata) if metadata is not None else None
        except TypeError:
            raise ValueError("Unable to serialize metadata.")

        session = self.metadata_getter()
        job_update_message: JobUpdateRequest = JobUpdateRequest(
            execution_id=execution_id,
            metadata=metadata_serial,
            cost=cost,
            gpu=gpu,
        )
        try:
            response: JobUpdateResponse = self.job_update_service_stub.job_update(
                job_update_message,
                metadata=session,
                wait_for_ready=True,
            )
            match response.WhichOneof("result"):
                case "empty":
                    return
                case "error":
                    logger.error(f"{response.error.message}, error code: {response.error.code}")
                case _:
                    logger.error("Failed to send job update: invalid response from the gRPC service.")
            raise RuntimeError("Failed to send job update.")
        except grpc.RpcError as e:
            logger.exception(
                f"JobUpdateRequest failed with error '{e.code().name}', message: '{e.details()}', "
                f"details: {e.trailing_metadata()}"
            )
            raise

    def close(self) -> None:
        """
        Close the GRPC channel.
        """
        logger.info("Closing GRPC channel at address `%s`.", self.grpc_address)
        self.grpc_channel.close()

    def __repr__(self) -> str:
        return f"JobUpdateClient(GRPC=True, {self.grpc_address})"

    def __enter__(self) -> "JobUpdateClient":
        """Enter context, return job update client as normal."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Exit context by closing the gRPC connect."""
        self.close()
