# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
