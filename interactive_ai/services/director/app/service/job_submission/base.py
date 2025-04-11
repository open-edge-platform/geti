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

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any

from geti_telemetry_tools import unified_tracing
from geti_types import ID
from grpc_interfaces.job_submission.client import GRPCJobsClient
from grpc_interfaces.job_submission.pb.job_service_pb2 import SubmitJobRequest


@dataclass(frozen=True)
class JobParams:
    priority: int
    job_name: str
    job_type: str
    key: str
    payload: dict
    metadata: dict
    duplicate_policy: str
    author: ID
    cancellable: bool = True
    project_id: ID | None = None
    gpu_num_required: int | None = None
    cost: list[SubmitJobRequest.CostRequest] | None = None


class ModelJobSubmitter(ABC):
    """
    An abstract base class for submitting model jobs.

    This class provides a common structure for submitting jobs to a model,
    with a standardized execution flow and an abstract method for data preparation.

    Attributes:
        jobs_client (GRPCJobsClient): A client for submitting jobs via gRPC.

    Methods:
        prepare_data: An abstract method to prepare job parameters.
        execute: A method to execute the job submission workflow.
    """

    def __init__(self, jobs_client: GRPCJobsClient):
        """
        Initialize the ModelJobSubmitter.

        Args:
            jobs_client: A client for submitting jobs via gRPC.
        """
        self.jobs_client = jobs_client

    @abstractmethod
    def prepare_data(self, **kwargs: Any) -> JobParams:
        """
        Prepares the necessary data for the job submission.

        This method should be implemented by subclasses to define how
        job parameters are prepared based on the input arguments.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            JobParams: The prepared parameters for job submission.
        """

    @unified_tracing
    def execute(self, **kwargs: Any) -> ID:
        """
        Common workflow for job submission.

        This method orchestrates the job submission process by preparing
        the data and then submitting the job using the jobs client.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            ID: The identifier of the submitted job.
        """
        params = self.prepare_data(**kwargs)
        return self.jobs_client.submit(**asdict(params))
