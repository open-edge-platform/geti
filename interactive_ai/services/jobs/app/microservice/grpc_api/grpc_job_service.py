# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the gRPC server for the job service microservice
"""

import json
import logging
import os
from concurrent import futures
from datetime import datetime
from json import JSONDecodeError

import grpc

from microservice.exceptions import DuplicateJobFoundException
from microservice.grpc_api.mappers.proto_mapper import JobToProto
from microservice.job_manager import JobManager, JobsAcl, JobSortingField, Pagination, SortDirection, TimestampFilter
from model.duplicate_policy import DuplicatePolicy
from model.job_state import JobStateGroup
from model.telemetry import Telemetry

from geti_spicedb_tools import Permissions, SpiceDB, SpiceDBResourceTypes
from geti_telemetry_tools import unified_tracing
from geti_types import ID
from grpc_interfaces.credit_system.client import InsufficientCreditsException
from grpc_interfaces.job_submission.pb.job_service_pb2 import (
    CancelJobRequest,
    EmptyResponse,
    FindJobsRequest,
    GetJobByIdRequest,
    GetJobsCountRequest,
    GetJobsCountResponse,
    JobIdResponse,
    JobResponse,
    ListJobsResponse,
    SubmitJobRequest,
)
from grpc_interfaces.job_submission.pb.job_service_pb2_grpc import JobServiceServicer, add_JobServiceServicer_to_server
from iai_core.session.session_propagation import setup_session_grpc

logger = logging.getLogger(__name__)

GRPC_MAX_MESSAGE_SIZE = int(os.environ.get("GRPC_MAX_MESSAGE_SIZE", 128 * 1024**2))

DEFAULT_N_JOBS_RETURNED = 10
MAX_N_JOBS_RETURNED = 50

MSG_ERR_DESERIALIZE_JOB_PAYLOAD = "Failed to deserialize the job payload. Please check the payload and try again."
MSG_ERR_DESERIALIZE_JOB_METADATA = "Failed to deserialize the job metadata. Please check the metadata and try again."
MSG_ERR_SERIALIZE_JOB_PAYLOAD = "Failed to serialize the job payload. Please check the payload and try again."
MSG_ERR_INSUFFICIENT_CREDITS = "Insufficient balance for job submission"
MSG_ERR_DUPLICATE_JOB = (
    "An identical job was found in the job queue. Please wait for the job to start running or "
    "delete it from the queue before submitting a new one. "
)
MSG_ERR_NOT_FOUND_JOB = "The requested job was not found. Please check the job ID and try again."
MSG_ERR_DUPLICATE_POLICY = "The supplied duplicate policy is invalid. Please provide a valid policy and try again."
MSG_ERR_TEMPLATE = "Request failed due to the following error: `{}`. Please try again later."


class GRPCJobService(JobServiceServicer):
    """
    This class implements JobServiceServicer interface to handle job submission,
    retrieval and deletion via gRPC protocol.
    """

    def __init__(self) -> None:
        self.job_manager = JobManager()

    @setup_session_grpc
    @unified_tracing
    def submit(self, request: SubmitJobRequest, context) -> JobIdResponse:  # noqa: ANN001
        """
        Submit a new job to the job service.

        :param request: the SubmitJobRequest containing the new job information
        :param context: the gRPC context for the request
        :return: a JobIdResponse containing the id of the submitted job
        :raises: JobPayloadNotDeserializableException if the payload is not deserializable
        """
        try:
            payload_dict = json.loads(request.payload)
        except JSONDecodeError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(MSG_ERR_DESERIALIZE_JOB_PAYLOAD)
            return JobIdResponse()
        try:
            metadata_dict = json.loads(request.metadata)
        except JSONDecodeError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(MSG_ERR_DESERIALIZE_JOB_METADATA)
            return JobIdResponse()

        try:
            duplicate_policy = DuplicatePolicy[request.duplicate_policy.upper()]
        except KeyError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(MSG_ERR_DUPLICATE_POLICY)
            return JobIdResponse()

        project_id = ID(request.project_id) if request.project_id else None
        author = ID(request.author)
        telemetry = Telemetry(context=request.telemetry.context)

        cost_requests = (
            {resource.unit: resource.amount for resource in request.cost}
            if request.cost is not None and len(request.cost) > 0
            else None
        )

        try:
            job_id = self.job_manager.submit(
                job_type=request.type,
                priority=request.priority,
                job_name=request.job_name,
                key=request.key,
                payload=payload_dict,
                metadata=metadata_dict,
                author=author,
                duplicate_policy=duplicate_policy,
                telemetry=telemetry,
                project_id=project_id,
                gpu_num_required=request.gpu_num_required,
                cost_requests=cost_requests,
                cancellable=request.cancellable,
            )
        except InsufficientCreditsException:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details(MSG_ERR_INSUFFICIENT_CREDITS)
            return JobIdResponse()
        except DuplicateJobFoundException:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details(MSG_ERR_DUPLICATE_JOB)
            return JobIdResponse()
        logger.info("Job with ID '%s' submitted by user_id: '%s'.", job_id, author)
        return JobIdResponse(id=job_id)

    @setup_session_grpc
    @unified_tracing
    def get_by_id(self, request: GetJobByIdRequest, context) -> JobResponse:  # noqa: ANN001
        """
        Get a job by its id.

        :param request: the GetJobByIdRequest containing the workspace_id and job_id to retrieve
        :param context: the gRPC context for the request
        :return: a JobResponse containing the job's information
        """
        job_id = ID(request.id)
        job = self.job_manager.get_by_id(job_id=job_id)
        if not job:
            logger.warning("Job with ID '%s' does not exist.")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(MSG_ERR_NOT_FOUND_JOB)
            return JobResponse()
        logger.info("Retrieving job with ID '%s'.", job.id)
        try:
            return JobToProto.forward(job)
        except ValueError:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(MSG_ERR_SERIALIZE_JOB_PAYLOAD)
            return JobResponse()

    @setup_session_grpc
    @unified_tracing
    def cancel(self, request: CancelJobRequest, context) -> EmptyResponse:  # noqa: ANN001, ARG002
        """
        Cancel a job by its ID.

        :param request: the CancelJobRequest containing the job ID
        :param context: the gRPC context for the request
        :return: EmptyResponse
        """
        job_id = ID(request.id)
        self.job_manager.mark_cancelled(job_id=job_id, user_uid=request.user_uid)
        logger.info("Job with ID '%s' is cancelled by user_id: '%s'.", job_id, request.user_uid)
        return EmptyResponse()

    @setup_session_grpc
    @unified_tracing
    def get_count(self, request: GetJobsCountRequest, context) -> GetJobsCountResponse:  # noqa: ANN001
        """
        Retrieves the number of jobs that match the filter criteria

        :param request: the GetJobsCountRequest containing the filter criteria
        :param context: the gRPC context for the request
        :return: GetJobsCountResponse containing the number of matching jobs
        """
        workspace_id = ID(request.workspace_id) if request.workspace_id else None
        job_types = [request.type] if request.type else None
        try:
            state_group = self._get_and_validate_state(state=request.state)
        except ValueError as err:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(MSG_ERR_TEMPLATE.format(err))
            return GetJobsCountResponse()
        project_id = ID(request.project_id) if request.project_id else None
        author_uid = request.author_uid if request.author_uid else None
        timestamp_filter: TimestampFilter | None = None
        if request.start_time_from or request.start_time_to:
            timestamp_filter = TimestampFilter(
                from_val=datetime.fromisoformat(request.start_time_from) if request.start_time_from else None,
                to_val=datetime.fromisoformat(request.start_time_to) if request.start_time_to else None,
            )

        workspace_jobs_author = None
        if author_uid is not None and request.all_permitted_jobs and workspace_id is not None:
            view_all_workspace_jobs = SpiceDB().check_permission(
                subject_type=SpiceDBResourceTypes.USER.value,
                subject_id=author_uid,
                resource_type=SpiceDBResourceTypes.WORKSPACE.value,
                resource_id=workspace_id,
                permission=Permissions.VIEW_ALL_WORKSPACE_JOBS.value,
            )
            if not view_all_workspace_jobs:
                workspace_jobs_author = author_uid

        permitted_projects = (
            [
                ID(project_id)
                for project_id in SpiceDB().get_user_projects(user_id=author_uid, permission=Permissions.VIEW_PROJECT)
            ]
            if author_uid is not None and request.all_permitted_jobs
            else None
        )
        acl = JobsAcl(
            permitted_projects=permitted_projects,
            workspace_jobs_author=workspace_jobs_author,
        )

        count = self.job_manager.get_jobs_count(
            workspace_id=workspace_id,
            job_types=job_types,
            state_group=state_group,
            project_id=project_id,
            key=request.key,
            author_uid=author_uid if not request.all_permitted_jobs else None,
            start_time=timestamp_filter,
            acl=acl,
        )
        logger.info("Number of jobs found: %d.", count)
        return GetJobsCountResponse(count=count)

    @setup_session_grpc
    @unified_tracing
    def find(self, request: FindJobsRequest, context) -> ListJobsResponse:  # noqa: ANN001
        """
        Find jobs based on the provided filters and return a stream of JobResponse

        :param request: the FindJobsRequest containing the filters to use for finding jobs
        :param context: the gRPC context for the request
        :return: ListJobsResponse object with the jobs matching the filter criteria and pagination info
        """
        job_types = [request.type] if request.type else None
        try:
            state_group = self._get_and_validate_state(state=request.state)
        except ValueError as err:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(MSG_ERR_TEMPLATE.format(err))
            return ListJobsResponse()
        workspace_id = ID(request.workspace_id)
        project_id = ID(request.project_id) if request.project_id else None
        author_uid = request.author_uid if request.author_uid else None
        timestamp_filter = (
            TimestampFilter(
                from_val=datetime.fromisoformat(request.start_time_from),
                to_val=datetime.fromisoformat(request.start_time_to),
            )
            if request.start_time_from and request.start_time_to
            else None
        )
        skip = request.skip if request.skip else 0
        limit = request.limit if request.limit else DEFAULT_N_JOBS_RETURNED
        pagination = Pagination(
            skip=max(skip, 0),
            limit=min(max(limit, 1), MAX_N_JOBS_RETURNED),
        )
        if skip != pagination.skip:
            logger.warning(
                "Requested pagination skip `%d` is out of bounds, resetting to `0`.",
                skip,
            )
        if limit != pagination.limit:
            logger.warning(
                "Requested pagination limit `%d` is out of bounds, resetting to `%d`.",
                limit,
                pagination.limit,
            )

        try:
            sort_by, sort_direction = self._get_and_validate_sorting_fields(
                sort_by=request.sort_by, sort_direction=request.sort_direction
            )
        except ValueError as err:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(MSG_ERR_TEMPLATE.format(err))
            return ListJobsResponse()

        workspace_jobs_author = None
        if author_uid is not None and request.all_permitted_jobs:
            view_all_workspace_jobs = SpiceDB().check_permission(
                subject_type=SpiceDBResourceTypes.USER.value,
                subject_id=author_uid,
                resource_type=SpiceDBResourceTypes.WORKSPACE.value,
                resource_id=workspace_id,
                permission=Permissions.VIEW_ALL_WORKSPACE_JOBS.value,
            )
            if not view_all_workspace_jobs:
                workspace_jobs_author = author_uid

        permitted_projects = (
            [
                ID(project_id)
                for project_id in SpiceDB().get_user_projects(user_id=author_uid, permission=Permissions.VIEW_PROJECT)
            ]
            if author_uid is not None and request.all_permitted_jobs
            else None
        )
        acl = JobsAcl(
            permitted_projects=permitted_projects,
            workspace_jobs_author=workspace_jobs_author,
        )

        total_count = self.job_manager.get_jobs_count(
            job_types=job_types,
            state_group=state_group,
            project_id=project_id,
            key=request.key,
            author_uid=author_uid if not request.all_permitted_jobs else None,
            start_time=timestamp_filter,
            acl=acl,
        )
        jobs = self.job_manager.find(
            job_types=job_types,
            state_group=state_group,
            project_id=project_id,
            key=request.key,
            author_uid=author_uid if not request.all_permitted_jobs else None,
            start_time=timestamp_filter,
            pagination=pagination,
            sort_by=sort_by,
            sort_direction=sort_direction,
            acl=acl,
        )

        num_retrieved_jobs = pagination.skip + len(jobs)
        logger.info("Retrieved %d/%d number of jobs.", num_retrieved_jobs, total_count)
        jobs_responses = [JobToProto.forward(job) for job in jobs]
        has_next_page = num_retrieved_jobs < total_count
        next_page = ListJobsResponse.NextPage(
            skip=num_retrieved_jobs,
            limit=pagination.limit,
        )
        return ListJobsResponse(
            jobs=jobs_responses,
            total_count=total_count,
            has_next_page=has_next_page,
            next_page=next_page if has_next_page else None,
        )

    @staticmethod
    def serve() -> None:
        """
        Start the server, and listen for requests.
        """
        grpc_port = os.environ.get("GRPC_JOB_SERVICE_PORT", "50051")
        address = f"[::]:{grpc_port}"
        logger.info(f"gRPC server version 0.1 on port {address}")
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ("grpc.max_send_message_length", GRPC_MAX_MESSAGE_SIZE),
                ("grpc.max_receive_message_length", GRPC_MAX_MESSAGE_SIZE),
            ],
        )
        add_JobServiceServicer_to_server(GRPCJobService(), server)
        server.add_insecure_port(address)
        server.start()
        server.wait_for_termination()

    @staticmethod
    def _get_and_validate_state(state: str | None = None) -> JobStateGroup | None:
        try:
            return JobStateGroup[state.upper()] if state else None
        except KeyError as err:
            raise ValueError(f"Invalid job state '{state}'.") from err

    @staticmethod
    def _get_and_validate_sorting_fields(
        sort_by: str | None, sort_direction: str | None
    ) -> tuple[JobSortingField | None, SortDirection | None]:
        try:
            _sort_by = JobSortingField[sort_by.upper()] if sort_by else None
        except KeyError as err:
            raise ValueError(f"Invalid sort_by '{sort_by}'.") from err
        try:
            _sort_direction = SortDirection[sort_direction.upper()] if sort_direction else None
        except KeyError as err:
            raise ValueError(f"Invalid sort_direction '{sort_direction}'.") from err
        return _sort_by, _sort_direction
