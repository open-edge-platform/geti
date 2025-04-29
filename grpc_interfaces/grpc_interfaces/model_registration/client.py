# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
import logging
import os
import pathlib
import time
from collections.abc import Callable, Iterable

import grpc

from .pb.service_pb2 import (
    Chunk,
    DownloadGraphRequest,
    Model,
    Project,
    PurgeProjectRequest,
    PurgeProjectResponse,
    RegisterRequest,
    StatusResponse,
)
from .pb.service_pb2_grpc import ModelRegistrationStub

logger = logging.getLogger(__name__)

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

MODEL_REGISTRATION_SERVICE = os.getenv("MODEL_REGISTRATION_SERVICE", "localhost:5555")
GRPC_MAX_MESSAGE_SIZE = int(os.environ.get("GRPC_MAX_MESSAGE_SIZE", 128 * 1024**2))  # noqa: PLW1508


class ModelRegistrationClient:
    """
    Client to interact with the model registration service via gRPC.

    :param metadata_getter: Lazy-evaluated function that returns the metadata to include
        in the gRPC request. It is typically used to propagate the session context.
        If the function returns None, then no metadata is propagated.
    """

    RETRY_MAX_ATTEMPTS = 5
    RETRY_INITIAL_BACKOFF = 1
    RETRY_MAX_BACKOFF = 4
    RETRY_BACKOFF_MULTIPLIER = 2

    def __init__(self, metadata_getter: Callable[[], tuple[tuple[str, str], ...] | None]) -> None:
        self.metadata_getter = metadata_getter
        self.grpc_channel = grpc.insecure_channel(
            MODEL_REGISTRATION_SERVICE,
            options=[
                (
                    "grpc.service_config",
                    json.dumps(
                        {
                            "methodConfig": [
                                {
                                    "name": [{"service": "service.ModelRegistration"}],  # <package>.<svc> from proto
                                    "retryPolicy": {
                                        "maxAttempts": self.RETRY_MAX_ATTEMPTS,
                                        "initialBackoff": f"{self.RETRY_INITIAL_BACKOFF}s",
                                        "maxBackoff": f"{self.RETRY_MAX_BACKOFF}s",
                                        "backoffMultiplier": self.RETRY_BACKOFF_MULTIPLIER,
                                        "retryableStatusCodes": ["UNAVAILABLE"],
                                    },
                                }
                            ]
                        }
                    ),
                ),
                ("grpc.max_send_message_length", GRPC_MAX_MESSAGE_SIZE),
                ("grpc.max_receive_message_length", GRPC_MAX_MESSAGE_SIZE),
            ],
        )
        self.model_registration_stub = ModelRegistrationStub(self.grpc_channel)

    def register(self, name: str, project: Project, models: list[Model], override: bool = False) -> None:
        """
        Register a model or pipeline of models

        :param name: Name of the model/pipeline. This will be used as identifier for the pipeline in ModelMesh
        :param project: Project in which the model/models live
        :param models: List of models to register
        :param override: If True, override any existing pipeline/model with the same `name`.
            If False, registration will fail in case a pipeline with the same name exists.
        """
        logger.info(f"Trying to register model {name} for project {project.id}")
        request = RegisterRequest(name=name, model=models, project=project, override=override)
        remaining_attempts = self.RETRY_MAX_ATTEMPTS
        backoff_time = self.RETRY_INITIAL_BACKOFF
        while remaining_attempts > 0:
            remaining_attempts -= 1
            try:
                response: StatusResponse = self.model_registration_stub.register_new_pipelines(
                    request, metadata=self.metadata_getter()
                )
            except grpc.RpcError as e:
                logger.error(f"RegisterRequest failed with error '{e.code().name}', message: '{e.details()}'")
                raise
            match response.status:
                case "CREATED":
                    logger.info(f"Model {name} has been successfully registered for project {project.id}")
                    return
                case "FAILED":
                    if remaining_attempts > 0:
                        logger.warning(
                            f"Registration request for model {name} failed with status '{response.status}'; "
                            f"{remaining_attempts} retry attempts left, trying again in {backoff_time} seconds"
                        )
                        time.sleep(backoff_time)
                        backoff_time = max(backoff_time * self.RETRY_BACKOFF_MULTIPLIER, self.RETRY_MAX_BACKOFF)
                    else:  # no attempts left
                        raise RuntimeError(f"Failed to register model {name}")
                case _:
                    logger.error(f"Got unknown response status when registering model {name}: {response.status}")

    def delete_project_pipelines(self, project_id: str) -> None:
        """
        Delete all inference pipelines for a project

        project_id: Identifier of the project
        """
        logger.info(f"Deleting all inference pipelines for project with ID: {project_id}...")
        request = PurgeProjectRequest(project_id=project_id)
        try:
            response: PurgeProjectResponse = self.model_registration_stub.delete_project_pipelines(
                request, metadata=self.metadata_getter()
            )
        except grpc.RpcError as e:
            logger.error(f"PurgeProjectRequest failed with error '{e.code().name}', message: '{e.details()}'")
            raise
        if response.success:
            logger.info(
                f"All inference services and inference model artifacts for project "
                f"{project_id} were removed successfully."
            )
        else:
            logger.error(
                f"Failed to delete all inference service and inference model artifacts "
                f"for project f{project_id}. Not all pipelines were removed "
                f"successfully. Check the logs of the model registration "
                f"microservice for details."
            )

    def download_graph(self, project: Project, models: list[Model], output_path: pathlib.Path) -> None:
        request = DownloadGraphRequest(project=project, models=models)
        try:
            chunks: Iterable[Chunk] = self.model_registration_stub.download_graph(
                request, metadata=self.metadata_getter()
            )
            with open(output_path, "wb") as f:
                for chunk in chunks:
                    f.write(chunk.buffer)
        except grpc.RpcError as e:
            logger.error(f"DownloadGraph failed with error '{e.code().name}', message: '{e.details()}'")
            raise

    def close(self) -> None:
        """Close the GRPC channel."""
        logger.info("Closing GRPC channel at address `%s`.", MODEL_REGISTRATION_SERVICE)
        self.grpc_channel.close()

    def __enter__(self) -> "ModelRegistrationClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.close()
