# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Controller for project export related requests"""

import logging
import os

from grpc import RpcError
from starlette.responses import RedirectResponse

from communication.http_exceptions import FailedArchiveDownloadException, FailedJobSubmissionException
from communication.job_creation_helpers import JobDuplicatePolicy, serialize_job_key
from repos import ZipStorageRepo

from geti_fastapi_tools.exceptions import ProjectNotFoundException
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier, Session
from grpc_interfaces.job_submission.client import GRPCJobsClient
from sc_sdk.entities.project import NullProject
from sc_sdk.repos import ProjectRepo
from sc_sdk.utils.naming_helpers import slugify

logger = logging.getLogger(__name__)

JOB_SERVICE_GRPC_ADDRESS = os.environ.get("JOB_SERVICE_ADDRESS", "localhost:50051")
PROJECT_EXPORT_TYPE = "export_project"


class ExportController:
    """
    The export controller submits the project export request to the job scheduler.
    """

    @classmethod
    def submit_project_export_job(cls, project_identifier: ProjectIdentifier, author_id: ID) -> ID:
        """
        Submit project export job to the job scheduler

        :param project_identifier: Identifier of the project to export
        :param author_id: ID of the user triggering the export job
        :return: submitted job id
        :raises FailedJobSubmissionException: if the export job cannot be submitted to the scheduler
        """
        project_to_export = ProjectRepo().get_by_id(project_identifier.project_id)
        if isinstance(project_to_export, NullProject):
            raise ProjectNotFoundException(project_identifier.project_id)

        job_payload = {
            "project_id": str(project_to_export.id_),
        }
        job_metadata = {
            "project": {
                "id": str(project_to_export.id_),
                "name": str(project_to_export.name),
            },
        }
        job_key = serialize_job_key(
            {
                "project_id": str(project_to_export.id_),
                "type": PROJECT_EXPORT_TYPE,
            }
        )
        with GRPCJobsClient(
            grpc_address=JOB_SERVICE_GRPC_ADDRESS,
            metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple(),
        ) as jobs_client:
            try:
                return jobs_client.submit(
                    priority=1,
                    job_name="Project Export",
                    job_type=PROJECT_EXPORT_TYPE,
                    key=job_key,
                    payload=job_payload,
                    metadata=job_metadata,
                    duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
                    author=author_id,
                    project_id=project_identifier.project_id,
                    cancellable=True,
                )
            except RpcError as rpc_error:
                logger.exception(f"Could not submit export job for project '{project_to_export.id_}'")
                raise FailedJobSubmissionException from rpc_error

    @classmethod
    def get_exported_archive_presigned_url(
        cls, project_identifier: ProjectIdentifier, export_operation_id: ID, domain_name: str
    ) -> RedirectResponse:
        """
        Get a pre-signed URL to download the exported project archive

        :param project_identifier: Identifier of the project being exported
        :param export_operation_id: ID of the export operation
        :param domain_name: Domain name associated with the download request.
            The download link will be generated with the same domain name.
        """
        try:
            internal_presigned_url = cls._get_zip_presigned_url(
                project_id=project_identifier.project_id, export_operation_id=export_operation_id
            )
        except Exception as exc:
            logger.exception(
                "Internal error while generating the pre-signed URL to download the exported project zip (id='%s')",
                export_operation_id,
            )
            raise FailedArchiveDownloadException from exc

        # Mangle the URL to hide internal S3 details from the user
        s3_internal_address = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        s3_external_address = domain_name + "/api/v1/fileservice"
        external_presigned_url = internal_presigned_url.replace(s3_internal_address, s3_external_address).replace(
            "http://", "https://"
        )

        headers = {
            "Content-Type": "application/zip",
            "Accept-Ranges": "bytes",  # Enable byte range support
        }
        return RedirectResponse(url=external_presigned_url, headers=headers)

    @staticmethod
    def _get_zip_presigned_url(project_id: ID, export_operation_id: ID) -> str:
        """
        Get a pre-signed URL to download the project archive

        :param project_id: ID of the project to export
        :param export_operation_id: ID of the export operation
        :return: Pre-signed URL to download the archive
        """
        session: Session = CTX_SESSION_VAR.get()
        zip_storage_repo = ZipStorageRepo(
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
        )
        project_repo = ProjectRepo()

        project_to_export = project_repo.get_by_id(project_id)
        download_file_name = (
            f"{slugify(project_to_export.name)}.zip"
            if not isinstance(project_to_export, NullProject)
            else "project.zip"
        )

        return zip_storage_repo.get_downloadable_archive_presigned_url(
            operation_id=export_operation_id,
            download_file_name=download_file_name,
        )
