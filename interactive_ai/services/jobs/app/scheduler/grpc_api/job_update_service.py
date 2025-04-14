# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


"""
This module implements the gRPC server for the job scheduler
"""

import json
import logging
import os
from concurrent import futures
from datetime import datetime
from json import JSONDecodeError

import grpc
from pymongo.errors import AutoReconnect

from model.job import JobConsumedResource
from scheduler.flyte import Flyte
from scheduler.state_machine import StateMachine

from geti_telemetry_tools import unified_tracing
from geti_types import ID
from grpc_interfaces.job_update.pb.job_update_service_pb2 import (
    EXECUTION_NOT_FOUND,
    INVALID_METADATA_UPDATE,
    Empty,
    Error,
    JobUpdateRequest,
    JobUpdateResponse,
)
from grpc_interfaces.job_update.pb.job_update_service_pb2_grpc import (
    JobUpdateServiceServicer,
    add_JobUpdateServiceServicer_to_server,
)
from sc_sdk.session.session_propagation import setup_session_grpc

logger = logging.getLogger(__name__)

GRPC_MAX_MESSAGE_SIZE = int(os.environ.get("GRPC_MAX_MESSAGE_SIZE", 128 * 1024**2))


class JobUpdateService(JobUpdateServiceServicer):
    """
    This class implements JobUpdateServiceServicer interface to handle job updates via gRPC protocol.
    """

    @setup_session_grpc
    @unified_tracing
    def job_update(self, request: JobUpdateRequest, context: grpc.ServicerContext) -> JobUpdateResponse:
        """
        Submit a new job to the job service.

        :param request: the SubmitJobRequest containing the new job information
        :param context: the gRPC context for the request
        :return: a JobIdResponse containing the id of the submitted job
        :raises: JobPayloadNotDeserializableException if the payload is not deserializable
        """
        logger.info(f"Job update request received: {request}")
        execution = Flyte().fetch_workflow_execution(execution_name=request.execution_id)

        if execution is None:
            logger.error(f"Unable to fetch execution {request.execution_id}")
            return JobUpdateResponse(error=Error(code=EXECUTION_NOT_FOUND))

        job_id = Flyte.get_execution_job_id(execution)

        try:
            if request.HasField("metadata"):
                try:
                    metadata_dict = json.loads(request.metadata)
                except JSONDecodeError:
                    return JobUpdateResponse(error=Error(code=INVALID_METADATA_UPDATE))
                StateMachine().update_metadata(job_id=ID(job_id), metadata=metadata_dict)

            if request.HasField("cost"):
                consumed_resources = [
                    JobConsumedResource(
                        amount=consumed.amount,
                        unit=consumed.unit,
                        consuming_date=datetime.fromtimestamp(consumed.consuming_date),
                        service=consumed.service,
                    )
                    for consumed in request.cost.consumed
                ]
                StateMachine().update_cost_consumed(job_id=ID(job_id), consumed_resources=consumed_resources)

            if request.HasField("gpu") and request.gpu.action == JobUpdateRequest.Gpu.RELEASE:
                StateMachine().set_gpu_state_released(job_id=ID(job_id))
        except AutoReconnect:
            logger.exception("Database connection has been lost")
            context.abort(code=grpc.StatusCode.UNAVAILABLE, details="Database connection has been lost")

        return JobUpdateResponse(empty=Empty())

    @staticmethod
    def serve() -> None:
        """
        Start the server, and listen for requests.
        """
        grpc_port = os.environ.get("GRPC_JOB_SCHEDULER_PORT", "50051")
        address = f"[::]:{grpc_port}"
        logger.info(f"gRPC server version 0.1 on port {address}")
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ("grpc.max_send_message_length", GRPC_MAX_MESSAGE_SIZE),
                ("grpc.max_receive_message_length", GRPC_MAX_MESSAGE_SIZE),
            ],
        )
        add_JobUpdateServiceServicer_to_server(JobUpdateService(), server)
        server.add_insecure_port(address)
        server.start()
        server.wait_for_termination()
