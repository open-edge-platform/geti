# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from os import getenv

from geti_types import CTX_SESSION_VAR, Singleton
from grpc_interfaces.job_submission.client import GRPCJobsClient

GRPC_ADDRESS = getenv("JOB_SERVICE_ADDRESS", "localhost:50051")


class JobsClient(metaclass=Singleton):
    """
    Singleton class to manage grpc jobs client instance
    """

    def __init__(self) -> None:
        self._jobs_client = None

    @property
    def jobs_client(self) -> GRPCJobsClient:
        """
        Creates GRCPJobsClient instance

        Note: grpc channel is closed during upon app shutdown

        Returns: instance of GRPCJobsClient
        """
        if not self._jobs_client:
            self._jobs_client = GRPCJobsClient(  # type: ignore
                grpc_address=GRPC_ADDRESS,
                metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple(),
            )
        return self._jobs_client  # type: ignore

    def stop(self) -> None:
        """
        Stops the gRPC job client

        This method should be called when the application is shutting down
        to ensure all resources are properly released.
        """
        if self._jobs_client:
            self._jobs_client.close()
