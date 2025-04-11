# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
"""
This module implements the import management usecase
"""

import logging

from communication.helpers.http_exceptions import (
    BadRequestGetiBaseException,
    FileNotFoundGetiBaseException,
    FileNotFullyUploadedGetiBaseException,
)
from communication.helpers.job_helper import JOB_SERVICE_GRPC_ADDRESS, JobDuplicatePolicy, JobType, serialize_job_key
from communication.repos.file_metadata_repo import FileMetadataRepo
from domain.entities.dataset_ie_file_metadata import ImportMetadata, NullFileMetadata
from domain.entities.geti_project_type import GetiProjectType

from geti_types import CTX_SESSION_VAR, ID
from grpc_interfaces.job_submission.client import GRPCJobsClient
from sc_sdk.entities.label import NullLabel
from sc_sdk.entities.project import NullProject
from sc_sdk.repos import LabelRepo, ProjectRepo

logger = logging.getLogger(__name__)


class ImportManager:
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
    def save_project_id(file_id: ID, project_id: ID) -> None:
        metadata_repo = FileMetadataRepo()
        file_metadata = metadata_repo.get_by_id(file_id)
        if isinstance(file_metadata, NullFileMetadata):
            logger.error("No dataset found for id %s", str(file_id))
            raise FileNotFoundGetiBaseException
        file_metadata.project_id = project_id
        metadata_repo.save(file_metadata)

    @staticmethod
    def get_validated_file_metadata(file_id: ID) -> ImportMetadata:
        """
        Validate that the dataset file is found and fully uploaded

        :param file_id: id of file to validate
        :return: import metadata of the valid import file
        """
        file_metadata = FileMetadataRepo().get_by_id(file_id)
        if isinstance(file_metadata, NullFileMetadata):
            logger.error("No dataset found for id %s", str(file_id))
            raise FileNotFoundGetiBaseException

        if file_metadata.size != file_metadata.offset or file_metadata.size == 0:
            logger.error("File with id %s not fully uploaded yet", file_id)
            raise FileNotFullyUploadedGetiBaseException

        if not isinstance(file_metadata, ImportMetadata):
            raise BadRequestGetiBaseException(
                f"Dataset with id {file_id} is an export dataset and cannot be used to import to project"
            )

        return file_metadata

    @staticmethod
    def validate_project_label_ids(project_id: str, label_ids_map: dict[str, str]) -> None:
        """
        Validate that the label ids in the label_ids_map are valid.

        :param project_id: ID of the project
        :param label_ids_map: map of dm label names to geti label ids in the given project
        :return: None (raise exception if there's an error)
        """
        project = ProjectRepo().get_by_id(ID(project_id))
        if isinstance(project, NullProject):
            raise BadRequestGetiBaseException(
                f"No project with given project id({project_id}) is found. Please verify provided ids."
            )

        label_repo = LabelRepo(project.identifier)
        for _, label_id in label_ids_map.items():
            label = label_repo.get_by_id(ID(label_id))
            if isinstance(label, NullLabel):
                raise BadRequestGetiBaseException("Given label ID in the labels_map is invalid.")

    def submit_prepare_import_to_new_project_job(
        self,
        import_id: ID,
        author: ID,
        metadata: dict,
    ) -> ID:
        """
        Submit prepare import to new project job

        :param import_id: ID of the dataset to import
        :param author: ID of the user triggering the job
        :param metadata: Metadata of the job
        :return: submitted job id
        """
        job_type = JobType.PREPARE_IMPORT_TO_NEW_PROJECT.value
        job_payload = {
            "import_id": str(import_id),
        }
        job_key = serialize_job_key(
            {
                "import_id": str(import_id),
                "type": job_type,
            }
        )
        return self.jobs_client.submit(
            priority=1,
            job_name="Prepare Import to New Project",
            job_type=job_type,
            key=job_key,
            payload=job_payload,
            metadata=metadata,
            duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
            author=author,
            cancellable=True,
        )

    def submit_prepare_import_to_existing_project_job(
        self,
        project_id: ID,
        import_id: ID,
        author: ID,
        metadata: dict,
    ) -> ID:
        """
        Submit prepare import to existing project job to the job scheduler

        :param project_id: ID of the project to import to
        :param import_id: ID of the dataset to import
        :param author: ID of the user triggering the job
        :param metadata: Metadata of the job
        :return: submitted job id
        """
        job_type = JobType.PREPARE_IMPORT_TO_EXISTING_PROJECT.value
        job_payload = {
            "project_id": str(project_id),
            "import_id": str(import_id),
        }
        job_key = serialize_job_key(
            {
                "project_id": str(project_id),
                "import_id": str(import_id),
                "type": str(job_type),
            }
        )
        return self.jobs_client.submit(
            priority=1,
            job_name="Prepare Import to Existing Project",
            job_type=job_type,
            key=job_key,
            payload=job_payload,
            metadata=metadata,
            duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
            author=author,
            project_id=project_id,
            cancellable=True,
        )

    def submit_perform_import_to_new_project_job(  # noqa: PLR0913
        self,
        import_id: ID,
        project_type: GetiProjectType,
        project_name: str,
        label_names: list[str],
        color_by_label: dict[str, str],
        keypoint_structure: dict[str, list[dict]],
        author: ID,
        metadata: dict,
    ) -> ID:
        """
        Submit perform import to new project job

        :param import_id: ID of the dataset to import
        :param project_type: Geti project type of project to create
        :param project_name: Name of the project to create
        :param label_names: List of labels to import form dataset
        :param color_by_label: Dictionary mapping label names to color
        :param keypoint_structure: keypoints edges and positions of default template
        :param author: ID of the user triggering the job
        :param metadata: Metadata of the job
        :return: submitted job id
        """
        job_type = JobType.PERFORM_IMPORT_TO_NEW_PROJECT.value
        job_payload = {
            "import_id": str(import_id),
            "project_type": project_type.name,
            "project_name": project_name,
            "label_names": label_names,
            "color_by_label": color_by_label,
            "keypoint_structure": keypoint_structure,
            "user_id": author,
        }
        job_key = serialize_job_key(
            {
                "import_id": str(import_id),
                "type": str(job_type),
            }
        )
        return self.jobs_client.submit(
            priority=1,
            job_name="Create Project from Dataset",
            job_type=job_type,
            key=job_key,
            payload=job_payload,
            metadata=metadata,
            duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
            author=author,
            cancellable=False,
        )

    def submit_perform_import_to_existing_project_job(
        self,
        project_id: ID,
        import_id: ID,
        labels_map: dict[str, str],
        dataset_storage_id: ID | None,
        dataset_name: str | None,
        author: ID,
        metadata: dict,
    ) -> ID:
        """
        Submit perform import to existing project job

        :param project_id: ID of the project to import to
        :param import_id: ID of the dataset to import
        :param labels_map: Map of label maps to geti label ids
        :param dataset_storage_id: ID of the dataset storage to import to
        :param dataset_name: Name of the new dataset to create and import to
        :param author: ID of the user triggering the job
        :param metadata: Metadata of the job
        :return: submitted job id
        """
        job_type = JobType.PERFORM_IMPORT_TO_EXISTING_PROJECT.value
        job_payload = {
            "import_id": str(import_id),
            "project_id": str(project_id),
            "labels_map": labels_map,
            "dataset_storage_id": str(dataset_storage_id) if dataset_storage_id else "",
            "dataset_name": dataset_name if dataset_name else "",
            "user_id": str(author),
        }
        job_key = serialize_job_key(
            {
                "import_id": str(import_id),
                "project_id": str(project_id),
                "type": str(job_type),
            }
        )
        return self.jobs_client.submit(
            priority=1,
            job_name="Import Dataset to Existing Project",
            job_type=job_type,
            key=job_key,
            payload=job_payload,
            metadata=metadata,
            duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
            author=author,
            project_id=project_id,
            cancellable=False,
        )
