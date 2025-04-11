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

"""Controller for project import related requests"""

import logging
import os

from grpc import RpcError

from communication.http_exceptions import FailedJobSubmissionException
from communication.job_creation_helpers import JobDuplicatePolicy, serialize_job_key
from communication.limit_check_helpers import check_max_number_of_projects
from communication.models import ImportOperation

from geti_types import CTX_SESSION_VAR, ID
from grpc_interfaces.job_submission.client import GRPCJobsClient

logger = logging.getLogger(__name__)

JOB_SERVICE_GRPC_ADDRESS = os.environ.get("JOB_SERVICE_ADDRESS", "localhost:50051")
PROJECT_IMPORT_TYPE = "import_project"


class ImportController:
    """
    The import controller submits the project import request to the job scheduler.
    """

    @classmethod
    def submit_project_import_job(cls, import_operation: ImportOperation, author_id: ID) -> ID:
        """
        Submit project import job to the job scheduler

        :param import_operation: contains information for the project import
        :param author_id: ID of the user triggering the import job
        :return: submitted job id
        :raises FailedJobSubmissionException: if the import job cannot be submitted to the scheduler
        """

        check_max_number_of_projects()

        job_payload = {
            "file_id": str(import_operation.file_id),
            "keep_original_dates": False,
            "project_name": import_operation.project_name if import_operation.project_name else "",
            "user_id": str(author_id),
        }
        job_metadata = {
            "parameters": {
                "file_id": str(import_operation.file_id),
            },
        }
        job_key = serialize_job_key(
            {
                "file_id": str(import_operation.file_id),
                "project_name": import_operation.project_name if import_operation.project_name else "",
                "type": PROJECT_IMPORT_TYPE,
            }
        )
        if import_operation.project_name:
            job_metadata["project"] = {"name": import_operation.project_name}
        logger.info(
            "Submitting request to import project to the job scheduler. Uploaded file id: `%s`",
            import_operation.file_id,
        )
        with GRPCJobsClient(
            grpc_address=JOB_SERVICE_GRPC_ADDRESS,
            metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple(),
        ) as jobs_client:
            try:
                return jobs_client.submit(
                    priority=1,
                    job_name="Project Import",
                    job_type=PROJECT_IMPORT_TYPE,
                    key=job_key,
                    payload=job_payload,
                    metadata=job_metadata,
                    duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
                    author=author_id,
                    cancellable=False,
                )
            except RpcError as rpc_error:
                logger.exception(f"Could not submit import job for file with id '{import_operation.file_id}'")
                raise FailedJobSubmissionException from rpc_error
