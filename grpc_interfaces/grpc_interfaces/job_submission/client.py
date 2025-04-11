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

import json
import logging
import os
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar, cast

from geti_telemetry_tools import ENABLE_TRACING, GrpcClientTelemetry, get_context_string
from geti_types import ID
from grpc import Channel, RpcError, insecure_channel  # type: ignore # grpc types not available in mypy
from readerwriterlock import rwlock

from .pb.job_service_pb2 import (
    CancelJobRequest,
    FindJobsRequest,
    GetJobByIdRequest,
    GetJobsCountRequest,
    GetJobsCountResponse,
    JobIdResponse,
    JobResponse,
    ListJobsResponse,
    SubmitJobRequest,
)
from .pb.job_service_pb2_grpc import JobServiceStub

logger = logging.getLogger(__name__)
TMethod = TypeVar("TMethod", bound=Callable[..., Any])

if ENABLE_TRACING:
    GrpcClientTelemetry.instrument()

GRPC_MAX_MESSAGE_SIZE = int(os.environ.get("GRPC_MAX_MESSAGE_SIZE", 128 * 1024**2))  # noqa: PLW1508


class CommunicationError(RuntimeError):
    """Exception for when a communication error occurs."""


class InsufficientBalanceException(CommunicationError):
    """Exception for when organization doesn't have enough credits for job submission."""


def grpc_requester(acquire_lock: bool = True):  # noqa: ANN201
    """
    Decorator for methods of GRPCJobsClient which handles GRPC requests.

    This decorator initialise the remote task if needed and handle GRPC errors.

    :param acquire_lock: Acquire the initialisation lock
    """

    def decorator(method: TMethod) -> TMethod:
        @wraps(method)
        def wrapper(self, *args, **kwargs):  # noqa: ANN001
            # TODO: Improve in scope of CVS-105988
            max_retries = 2

            for _ in range(max_retries):
                try:
                    if acquire_lock:
                        if method.__name__ in ["submit", "cancel"]:
                            with self._GRPCJobsClient__init_lock.gen_wlock():
                                return method(self, *args, **kwargs)
                        else:
                            with self._GRPCJobsClient__init_lock.gen_rlock():
                                return method(self, *args, **kwargs)
                    else:
                        return method(self, *args, **kwargs)
                except RpcError as ex:
                    self.handle_grpc_error(ex)

        return cast("TMethod", wrapper)

    return decorator


class GRPCJobsClient:
    """
    Client to interact with the jobs microservice via gRPC.

    :param grpc_address: Address of the gRPC server.
    :param metadata_getter: Lazy-evaluated function that returns the metadata to include
        in the gRPC request. It is typically used to propagate the session context.
    :raises ValueError: If metadata_getter returns None
    """

    grpc_channel: Channel
    grpc_address: str
    job_service_stub: JobServiceStub
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

    def __init__(self, grpc_address: str, metadata_getter: Callable[[], tuple[tuple[str, str], ...]]) -> None:
        self.metadata_getter = metadata_getter
        if not self.metadata_getter():
            raise ValueError("Unable to get session from metadata")
        if grpc_address is None:
            raise ValueError("GRPC address not set, cannot setup a channel to given microservice")
        self.grpc_address = grpc_address
        logger.info("Initializing GRPCJobsClient on address `%s`.", self.grpc_address)
        self.grpc_channel = insecure_channel(
            self.grpc_address,
            options=[
                ("grpc.service_config", self.grpc_channel_config),
                ("grpc.max_send_message_length", GRPC_MAX_MESSAGE_SIZE),
                ("grpc.max_receive_message_length", GRPC_MAX_MESSAGE_SIZE),
            ],
        )

        # This lock has two purposes:
        # * to make sure that we don't run the initialisation multiple times from separate threads.
        # * to make sure that we don't reset the task simultaneously to another GRPC call
        # We use a reader/writer lock to allow concurrent GRPC calls (reader mode) unless
        # one of the call is a submit/cancel call (writer mode).
        self.__init_lock = rwlock.RWLockWrite()

        self.job_service_stub = JobServiceStub(self.grpc_channel)

    @grpc_requester()
    def submit(  # noqa: PLR0913
        self,
        priority: int,
        job_name: str,
        job_type: str,
        key: str,
        payload: dict,
        metadata: dict,
        duplicate_policy: str,
        author: ID,
        cancellable: bool = True,
        project_id: ID | None = None,
        gpu_num_required: int | None = None,
        cost: list[SubmitJobRequest.CostRequest] | None = None,
    ) -> ID:
        """
        Sends a request to submit a job to the job scheduler through the gRPC server.

        :param priority: job's priority
        :param job_name: job's name
        :param job_type: job's type
        :param key: job's key
        :param payload: job's payload containing data required for its execution
        :param metadata: job's metadata
        :param duplicate_policy: policy to adopt in case of duplicate job
        :param author: job's author
        :param cancellable: flag, defining if job can be cancelled after startup
        :param project_id: job's project ID
        :param gpu_num_required: number of GPUs required for job execution
        :param cost: cost of the training job
        :return: the id of the submitted job
        :raises: ValueError if the payload is not serializable
        """
        try:
            payload_serial = json.dumps(payload)
        except TypeError:
            raise ValueError("Unable to serialize payload.")
        try:
            metadata_serial = json.dumps(metadata)
        except TypeError:
            raise ValueError("Unable to serialize metadata.")

        session = self.metadata_getter()
        submit_message: SubmitJobRequest = SubmitJobRequest(
            priority=priority,
            workspace_id=dict(session)["workspace_id"],
            job_name=job_name,
            type=job_type,
            key=key,
            payload=payload_serial,
            metadata=metadata_serial,
            duplicate_policy=duplicate_policy,
            author=author,
            project_id=project_id,  # type: ignore
            telemetry=SubmitJobRequest.Telemetry(context=get_context_string()),
            gpu_num_required=gpu_num_required,
            cost=cost,
            cancellable=cancellable,
        )
        reply: JobIdResponse = self.job_service_stub.submit(
            submit_message,
            metadata=session,
            wait_for_ready=True,
        )
        return ID(reply.id)

    @grpc_requester()
    def find(  # noqa: PLR0913
        self,
        workspace_id: ID,
        job_type: str | None = None,
        state: str | None = None,
        project_id: ID | None = None,
        author_uid: str | None = None,
        start_time_from: datetime | None = None,
        start_time_to: datetime | None = None,
        limit: int | None = None,
        skip: int | None = None,
        sort_by: str | None = None,
        sort_direction: str | None = None,
        all_permitted_jobs: bool = False,
    ) -> ListJobsResponse:
        """
        Sends a request to find jobs through the gRPC server.

        :param workspace_id: the ID of the workspace
        :param job_type: the type of job to filter on
        :param state: the state of the jobs to filter on
        :param project_id: the ID of the project which the jobs belong
        :param author_uid: the user id of the author of the jobs
        :param start_time_from: the start time to filter on
        :param start_time_to: the end time to filter on
        :param limit: amount of items to limit per page for pagination
        :param skip: how many items to skip ahead of. Used for pagination
        :param sort_by: Sorting field to sort by
        :param sort_direction: Sorting direction
        :param all_permitted_jobs: whether to get all permitted jobs that a user has access to. Requires author_uid.
        :return: the list of found jobs
        """
        find_message: FindJobsRequest = FindJobsRequest(
            workspace_id=str(workspace_id),
            type=job_type,  # type: ignore
            state=state,  # type: ignore
            project_id=project_id,  # type: ignore
            author_uid=author_uid,  # type: ignore
            start_time_from=(start_time_from.isoformat() if start_time_from is not None else None),  # type: ignore
            start_time_to=(
                start_time_to.isoformat() if start_time_to is not None else None  # type: ignore
            ),  # type: ignore
            limit=limit,  # type: ignore
            skip=skip,  # type: ignore
            sort_by=sort_by,  # type: ignore
            sort_direction=sort_direction,  # type: ignore
            all_permitted_jobs=all_permitted_jobs,
        )
        reply: ListJobsResponse = self.job_service_stub.find(
            find_message, metadata=self.metadata_getter(), wait_for_ready=True
        )
        return reply

    @grpc_requester()
    def get_by_id(self, job_id: ID) -> JobResponse | None:
        """
        Sends a request to get a job by id through the gRPC server.

        :param job_id: the id the job to get
        :return: the found job or None
        """
        session = self.metadata_getter()
        get_job_message: GetJobByIdRequest = GetJobByIdRequest(workspace_id=dict(session)["workspace_id"], id=job_id)
        return self.job_service_stub.get_by_id(get_job_message, metadata=session, wait_for_ready=True)

    @grpc_requester()
    def cancel(self, job_id: ID, user_uid: str) -> None:
        """
        Sends a request to cancel a job through the gRPC server.
        """
        session = self.metadata_getter()
        cancel_message: CancelJobRequest = CancelJobRequest(
            workspace_id=dict(session)["workspace_id"], id=job_id, user_uid=user_uid
        )
        self.job_service_stub.cancel(cancel_message, metadata=session, wait_for_ready=True)

    @grpc_requester()
    def get_count(  # noqa: PLR0913
        self,
        workspace_id: ID | None = None,
        job_type: str | None = None,
        state: str | None = None,
        project_id: ID | None = None,
        author_uid: str | None = None,
        start_time_from: datetime | None = None,
        start_time_to: datetime | None = None,
        all_permitted_jobs: bool = False,
    ) -> int:
        """
        Sends a request to the gRPC server to get the number of jobs matching the given parameters.

        :param workspace_id: the ID of the workspace
        :param job_type: the type of job to filter on
        :param state: the state of the jobs to filter on
        :param project_id: the ID of the project which the jobs belong
        :param author_uid: the user id of the author of the jobs
        :param start_time_from: the start time to filter on
        :param start_time_to: the end time to filter on
        :param all_permitted_jobs: whether to count all permitted jobs that a user has access to. Requires author_uid.
        :return: the number of jobs matching the search criteria
        """
        get_count_message: GetJobsCountRequest = GetJobsCountRequest(
            workspace_id=str(workspace_id) if workspace_id is not None else "",
            type=job_type or "",
            state=state or "",
            project_id=project_id or "",
            author_uid=author_uid or "",
            start_time_from=(start_time_from.isoformat() if start_time_from is not None else ""),
            start_time_to=(start_time_to.isoformat() if start_time_to is not None else ""),
            all_permitted_jobs=all_permitted_jobs,
        )
        reply: GetJobsCountResponse = self.job_service_stub.get_count(
            get_count_message, metadata=self.metadata_getter(), wait_for_ready=True
        )
        return reply.count

    def close(self) -> None:
        """
        Close the GRPC channel.
        """
        logger.info("Closing GRPC channel at address `%s`.", self.grpc_address)
        self.grpc_channel.close()

    def __repr__(self) -> str:
        return f"GRPCJobsClient(GRPC=True, {self.grpc_address})"

    def __enter__(self) -> "GRPCJobsClient":
        """Enter context, return jobs client as normal."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Exit context by closing the gRPC connect."""
        self.close()

    @grpc_requester()
    # TODO: refactor error handling in CVS-145817
    def handle_grpc_error(self, error: RpcError) -> None:
        """
        Handle a GRPC error. This function re-raise the exception with a user-friendly message.

        :param error: grpc error
        :raises CommunicationError: if the error is not handled and re-raised.
        """
        details = str(error.details()) if hasattr(error, "details") else ""
        code = error.code() if hasattr(error, "code") else None

        logger.exception(
            "The GRPC request failed with exception: %s, details: `%s`, code: `%s`",
            str(error),
            details,
            code,
        )

        if "Insufficient balance" in details:
            raise InsufficientBalanceException(details) from error

        if not details:
            details = "Request failed due to unknown issues. Please try again later."

        raise CommunicationError(details) from error
