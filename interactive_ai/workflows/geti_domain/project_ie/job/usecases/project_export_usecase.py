# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the project export usecase.
"""

import logging
import os
import tempfile
import uuid
from collections.abc import Callable
from datetime import timezone
from functools import partial

from bson.binary import UuidRepresentation
from bson.json_util import DatetimeRepresentation, JSONOptions, dumps
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier, Session
from iai_core.repos.base import SessionBasedRepo
from iai_core.utils.iteration import multi_map
from iai_core.versioning import DataVersion
from jobs_common.tasks.utils.progress import publish_metadata_update

from job.entities import ProjectZipArchive, ProjectZipArchiveWrapper
from job.entities.exceptions import ExportProjectFailedException
from job.repos.binary_storage_repo import BinaryStorageRepo
from job.repos.document_repo import DocumentRepo
from job.repos.zip_storage_repo import ZipStorageRepo
from job.usecases.data_redaction_usecase import ExportDataRedactionUseCase
from job.usecases.signature_usecase import SignatureUseCaseHelper
from job.utils.file_utils import read_file_in_chunks

logger = logging.getLogger(__name__)


class ProjectExportUseCase:
    """The ProjectExportUseCase coordinates the main operations for the export process"""

    COLLECTIONS_WITH_MEDIA_BASED_ID = ["active_score", "dataset_storage_filter_data"]
    COLLECTIONS_FOR_EVALUATION_RESULTS = ["model_test_result", "evaluation_result"]
    COLLECTIONS_WITH_LOCKS = ["project"]

    @classmethod
    def __export_as_zip(
        cls,
        project_id: ID,
        tmp_folder: str,
        progress_callback: Callable[[float, str], None],
    ) -> None:
        """
        Create a zip file containing all the data of the project to export

        :param project_id: ID of the project to export
        :param tmp_folder: Temporary local folder that can be used to store files
        :param progress_callback: callback function to report progress
        """
        session: Session = CTX_SESSION_VAR.get()
        project_identifier = ProjectIdentifier(workspace_id=session.workspace_id, project_id=project_id)
        data_redaction_use_case = ExportDataRedactionUseCase()
        document_repo = DocumentRepo(project_identifier=project_identifier)
        binary_storage_repo = BinaryStorageRepo(
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            project_id=project_id,
        )
        zip_storage_repo = ZipStorageRepo(
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
        )
        json_options = JSONOptions(
            uuid_representation=UuidRepresentation.STANDARD,
            datetime_representation=DatetimeRepresentation.ISO8601,
            tz_aware=True,
            tzinfo=timezone.utc,
        )

        # Create the zip file in a local temporary folder
        logger.info("Creating zip archive to export project '%s'", project_id)
        project_archive_path = os.path.join(tmp_folder, ProjectZipArchiveWrapper.PROJECT_ARCHIVE)
        with ProjectZipArchive(zip_file_path=project_archive_path) as zip_archive:
            # Fetch MongoDB documents, redact them and finally add them to the zip archive
            logger.info(
                "Exporting the documents from DB collections for project '%s'",
                project_id,
            )
            progress_callback(25, "Exporting project database")
            collection_names = document_repo.get_collection_names()
            for collection_name in collection_names:
                db_raw_documents = document_repo.get_all_documents_from_db_for_collection(
                    collection_name=collection_name
                )
                lock_redaction: list[Callable] = (
                    [data_redaction_use_case.remove_lock_in_mongodb_doc]
                    if collection_name in ProjectExportUseCase.COLLECTIONS_WITH_LOCKS
                    else []
                )
                media_based_id_redaction: list[Callable] = (
                    [data_redaction_use_case.replace_media_based_objectid_in_mongodb_doc]
                    if collection_name in ProjectExportUseCase.COLLECTIONS_WITH_MEDIA_BASED_ID
                    else []
                )
                redacted_docs = multi_map(
                    db_raw_documents,
                    data_redaction_use_case.remove_container_info_in_mongodb_doc,
                    data_redaction_use_case.remove_job_id_in_mongodb_doc,
                    *lock_redaction,
                    *media_based_id_redaction,
                    partial(dumps, json_options=json_options),
                    data_redaction_use_case.replace_objectid_in_mongodb_doc,
                    data_redaction_use_case.replace_objectid_based_binary_filename_in_mongodb_doc,
                    data_redaction_use_case.mask_user_info_in_mongodb_doc,
                )
                # Note: 'db_raw_documents' and 'redacted_docs' are generators, piped and lazily evaluated,
                # so any error raised while fetching/redacting documents is actually thrown in the next write stage
                try:
                    zip_archive.add_collection_with_documents(collection_name=collection_name, documents=redacted_docs)
                except Exception:  # log the collection name before re-raising the exception
                    logger.error(
                        "Error occurred while exporting collection '%s'",
                        collection_name,
                    )
                    raise

            progress_callback(50, "Exporting project binary files")
            # Fetch binary objects from S3, adjust their paths and finally add them to the zip archive
            logger.info("Exporting binary objects from S3 storage for project '%s'", project_id)
            for object_type in binary_storage_repo.get_object_types():
                objects_local_and_remote_paths = binary_storage_repo.get_all_objects_by_type(
                    object_type=object_type, target_folder=tmp_folder
                )
                redacted_objects_paths = (
                    (
                        data_redaction_use_case.replace_objectid_in_file(lp),  # redact the file
                        data_redaction_use_case.replace_objectid_in_url(rp),  # redact the path
                    )
                    for lp, rp in objects_local_and_remote_paths
                )
                zip_archive.add_objects_by_type(
                    object_type=object_type,
                    local_and_remote_paths=redacted_objects_paths,
                )

            # Add the manifest
            logger.info("Adding manifest to the archive of exported project '%s'", project_id)
            zip_archive.add_manifest(
                version=DataVersion.get_current().version_string,
                min_id=data_redaction_use_case.objectid_replacement_min_id,
            )

        # Generate digital signature
        export_signature_use_case = SignatureUseCaseHelper.get_signature_use_case()
        project_zip_data = read_file_in_chunks(filename=project_archive_path)
        signature = export_signature_use_case.generate_signature(data=project_zip_data)

        # Pack up the project data (zip), public key and signature
        zip_file_path = os.path.join(tmp_folder, f"{str(uuid.uuid4())}.zip")
        with ProjectZipArchiveWrapper(zip_file_path=zip_file_path) as wrapper_zip_archive:
            wrapper_zip_archive.add_project_archive(project_archive_path=project_archive_path)
            wrapper_zip_archive.add_signature(signature=signature)
            wrapper_zip_archive.add_public_key(public_key=export_signature_use_case.public_key_bytes)

        # Upload the archive to S3 for later download
        progress_callback(75.0, "Preparing zip archive")
        export_operation_id = SessionBasedRepo.generate_id()
        zip_storage_repo.upload_downloadable_archive(operation_id=export_operation_id, zip_local_path=zip_file_path)

        download_url = cls._get_download_url(
            organization_id=session.organization_id,
            project_identifier=project_identifier,
            export_operation_id=export_operation_id,
        )
        metadata = {
            "download_url": download_url,
            "size": zip_archive.get_compressed_size(),  # bytes
        }
        publish_metadata_update(metadata=metadata)
        logger.info("Project '%s' has been successfully exported", project_id)

    @staticmethod
    def export_as_zip(project_id: ID, progress_callback: Callable[[float, str], None]) -> None:
        """
        Create a zip file containing all the data of the project to export

        :param project_id: ID of the project to export
        :param progress_callback: callback function to report progress
        """
        try:
            with tempfile.TemporaryDirectory() as tmp_dir_path:
                ProjectExportUseCase.__export_as_zip(
                    project_id=project_id,
                    tmp_folder=tmp_dir_path,
                    progress_callback=progress_callback,
                )
        except Exception as exc:
            logger.exception("Failed to export project with id '%s'.", project_id)
            # Exceptions that inherit from ExportProjectFailedException already have a user-friendly message,
            # so they can be re-raised as they are. Other exceptions should be converted to
            # a ExportProjectFailedException with a generic message.
            if isinstance(exc, ExportProjectFailedException):
                raise exc
            raise ExportProjectFailedException from exc

    @staticmethod
    def _get_download_url(
        organization_id: ID,
        project_identifier: ProjectIdentifier,
        export_operation_id: ID,
    ) -> str:
        """
        Returns the download URL for the project export zip archive

        :param organization_id: ID of organization to which the project belongs
        :param project_identifier: Identifier of the project to export
        :param export_operation_id: ID of the export operation
        :returns: the URL for the download endpoint
        """
        return (
            f"api/v1/organizations/{organization_id}/workspaces/{project_identifier.workspace_id}/"
            f"projects/{project_identifier.project_id}/exports/{export_operation_id}/download"
        )
