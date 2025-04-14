# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the export management usecase
"""

import logging
from typing import NamedTuple

from communication.helpers.job_helper import JOB_SERVICE_GRPC_ADDRESS, JobDuplicatePolicy, JobType, serialize_job_key
from communication.repos.object_storage_repo import ObjectDataRepo
from domain.entities.dataset_ie_file_metadata import ExportFormat

from geti_types import CTX_SESSION_VAR, ID, Session
from grpc_interfaces.job_submission.client import GRPCJobsClient

logger = logging.getLogger(__name__)


class DatasetExportOperationConfig(NamedTuple):
    """
    Configuration class for dataset export operations.

    Attributes:
        export_format (ExportFormat): Specifies the format for exporting data
        include_unannotated (bool): Whether to include unannotated media in export
        save_video_as_images (bool): Whether to export video as frame images or not.
    """

    export_format: ExportFormat
    include_unannotated: bool
    save_video_as_images: bool


class ExportManager:
    def __init__(self) -> None:
        self._jobs_client: GRPCJobsClient | None = None  # initialized lazily

    @property
    def jobs_client(self) -> GRPCJobsClient:
        """Initialize and/or get the gRPC client to submit jobs"""
        if self._jobs_client is None:
            self._jobs_client = GRPCJobsClient(
                grpc_address=JOB_SERVICE_GRPC_ADDRESS, metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple()
            )
        return self._jobs_client

    @staticmethod
    def get_exported_dataset_presigned_url(file_id: ID, filename: str) -> str:
        """
        Return location of zipped file with id

        :param file_id: id of file
        :param filename: Filename to set for the file at the URL
        :return: Presigned URL pointing to zipped file for given id
        """
        object_data_repo = ObjectDataRepo()
        return object_data_repo.get_zipped_dataset_presigned_url(id_=file_id, filename=filename)

    def submit_export_job(
        self,
        project_id: ID,
        dataset_storage_id: ID,
        export_config: DatasetExportOperationConfig,
        author: ID,
        metadata: dict,
    ) -> ID:
        """
        Submit export job to the job scheduler

        :param project_id: ID of the project to be exported
        :param dataset_storage_id: ID of the dataset storage to be exported
        :param export_config: Configuration for exporring the dataset
        :param author: ID of the user triggering export job
        :param metadata: metadata for export job
        :return: submitted job id
        """
        session: Session = CTX_SESSION_VAR.get()
        export_job_type = JobType.EXPORT_DATASET.value
        job_payload = {
            "organization_id": str(session.organization_id),
            "project_id": str(project_id),
            "dataset_storage_id": str(dataset_storage_id),
            "include_unannotated": export_config.include_unannotated,
            "export_format": export_config.export_format.value,
            "save_video_as_images": export_config.save_video_as_images,
        }
        job_key = {
            "dataset_storage_id": str(dataset_storage_id),
            "include_unannotated": export_config.include_unannotated,
            "export_format": export_config.export_format.value,
            "save_video_as_images": export_config.save_video_as_images,
            "type": export_job_type,
        }

        return self.jobs_client.submit(
            priority=1,
            job_name="Dataset Export",
            job_type=export_job_type,
            key=serialize_job_key(job_key),
            payload=job_payload,
            metadata=metadata,
            duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
            author=author,
            project_id=project_id,
            cancellable=True,
        )
