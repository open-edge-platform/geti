# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the project import usecase.
"""

import logging
import os
import tempfile
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import timezone
from functools import partial

from bson.binary import UuidRepresentation
from bson.json_util import DatetimeRepresentation, JSONOptions, loads
from geti_kafka_tools import publish_event
from geti_spicedb_tools import SpiceDB
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier, Session
from grpc_interfaces.model_registration.client import ModelRegistrationClient
from iai_core.entities.model import NullModel
from iai_core.repos import ProjectRepo
from iai_core.repos.mappers import IDToMongo
from iai_core.repos.storage.storage_client import BinaryObjectType
from iai_core.services import ModelService
from iai_core.utils.iteration import multi_map
from iai_core.versioning import DataVersion
from jobs_common.tasks.utils.progress import publish_metadata_update

from job.entities import ProjectZipArchive, ProjectZipArchiveWrapper
from job.entities.exceptions import (
    ImportProjectFailedException,
    ImportProjectUnsupportedVersionException,
    ProjectUpgradeFailedException,
)
from job.repos import BinaryStorageRepo, DocumentRepo
from job.repos.zip_storage_repo import ZipStorageRepo
from job.usecases import DataMigrationUseCase, ImportDataRedactionUseCase
from job.usecases.signature_usecase import PublicKeyBytes, SignatureUseCaseHelper
from job.usecases.update_metrics_usecase import UpdateMetricsUseCase
from job.utils.file_utils import read_file_in_chunks
from job.utils.model_registration_utils import ModelMapper, ProjectMapper

logger = logging.getLogger(__name__)


class ProjectImportUseCase:
    """
    The ProjectImportUseCase coordinates the main operations for the import process

    :param keep_original_dates: if True original exported dates are kept
    :param project_name: name to use for the newly imported project
    """

    COLLECTIONS_WITH_MEDIA_BASED_ID = ["active_score", "dataset_storage_filter_data"]

    def __init__(
        self,
        keep_original_dates: bool = False,
        project_name: str | None = None,
    ):
        self.keep_original_dates = keep_original_dates
        self.project_name = project_name if project_name else None
        # set when the import operation is started
        self.project_id: ID | None = None

    @staticmethod
    def _download_import_zip(file_id: ID, local_zip_path: str) -> None:
        """
        Download an uploaded importable project to the local storage so it can be handled by the import process in an
        easier way.

        :param file_id: Operation ID for the upload/import operation
        :param local_zip_path: Target path for the local zip file to be downloaded to
        """
        session: Session = CTX_SESSION_VAR.get()
        ZipStorageRepo(
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
        ).download_import_zip(operation_id=file_id, target_local_path=local_zip_path)

    @staticmethod
    def _delete_import_zip(file_id: ID) -> None:
        """
        Delete the uploaded zip archive from the object storage

        :param file_id: Operation ID for the upload/import operation
        """
        session: Session = CTX_SESSION_VAR.get()
        try:
            ZipStorageRepo(
                organization_id=session.organization_id,
                workspace_id=session.workspace_id,
            ).delete_import_zip(operation_id=file_id)
        except Exception as exc:
            # Log a warning and continue
            logger.warning(
                f"An error occurred while trying to delete temporary files from the object storage. Reason: {str(exc)}"
            )

    @staticmethod
    def _register_active_models(project_identifier: ProjectIdentifier) -> None:
        """
        Register the active model (if any) of every task so that it can be used for inference

        :param project_identifier: Identifier of the imported project
        """
        session = CTX_SESSION_VAR.get()
        project_repo = ProjectRepo()
        project = project_repo.get_by_id(project_identifier.project_id)
        trainable_tasks = project.get_trainable_task_nodes()
        active_base_models = [
            ModelService.get_base_active_model(project_identifier=project_identifier, task_node_id=task_node.id_)
            for task_node in trainable_tasks
        ]
        active_inference_models = [
            ModelService.get_inference_active_model(project_identifier=project_identifier, task_node_id=task_node.id_)
            for task_node in trainable_tasks
        ]
        project_is_single_task: bool = len(trainable_tasks) == 1
        first_task_has_model: bool = not isinstance(active_base_models[0], NullModel)
        second_task_has_model: bool = not project_is_single_task and not isinstance(active_base_models[1], NullModel)
        if not first_task_has_model and not second_task_has_model:
            return  # fast path: no models to register

        proto_project = ProjectMapper.forward(project)
        proto_active_models = [
            ModelMapper.forward(
                model=base_model,
                organization_id=session.organization_id,
                workspace_id=session.workspace_id,
                project_id=project.id_,
                task_id=task.id_,
                optimized_model_id=optimized_model.id_,
            )
            for task, base_model, optimized_model in zip(trainable_tasks, active_base_models, active_inference_models)
        ]

        with ModelRegistrationClient(metadata_getter=lambda: session.as_tuple()) as client:
            if project_is_single_task:
                if first_task_has_model:
                    logger.info(
                        f"Registering first task active model of project '{project.id_}' as '{str(project.id_)}-active'"
                    )
                    client.register(
                        name=f"{str(project.id_)}-active",
                        project=proto_project,
                        models=proto_active_models[:1],
                        override=True,
                    )
            else:  # task-chain project
                if first_task_has_model:
                    # Register the first model for task inference ('-{task}')
                    logger.info(
                        f"Registering first task active model of project '{project.id_}'"
                        f"as '{str(project.id_)}-{str(trainable_tasks[0].id_)}'"
                    )
                    client.register(
                        name=f"{str(project.id_)}-{str(trainable_tasks[0].id_)}",
                        project=proto_project,
                        models=proto_active_models[:1],
                        override=True,
                    )
                    if second_task_has_model:  # both tasks have a trained model
                        # Use both models for pipeline inference ('-active')
                        logger.info(
                            f"Registering both active models of project '{project.id_}' as '{str(project.id_)}-active'"
                        )
                        client.register(
                            name=f"{str(project.id_)}-active",
                            project=proto_project,
                            models=proto_active_models,
                            override=True,
                        )
                    else:  # only the first task has a trained model
                        # Use the first model alone for pipeline inference ('-active')
                        logger.info(
                            f"Registering first task active model of project '{project.id_}' "
                            f"as '{str(project.id_)}-active'"
                        )
                        client.register(
                            name=f"{str(project.id_)}-active",
                            project=proto_project,
                            models=proto_active_models[:1],
                            override=True,
                        )
                if second_task_has_model:
                    # Register the second model for task inference ('-{task}')
                    logger.info(
                        f"Registering second task active model of project '{project.id_}' "
                        f"as '{str(project.id_)}-{str(trainable_tasks[1].id_)}'"
                    )
                    client.register(
                        name=f"{str(project.id_)}-{str(trainable_tasks[1].id_)}",
                        project=proto_project,
                        models=proto_active_models[1:2],
                        override=True,
                    )

    def __extract_project_document(
        self,
        zip_archive: ProjectZipArchive,
        data_redaction_use_case: ImportDataRedactionUseCase,
        json_options: JSONOptions,
    ) -> dict:
        """
        Extract and redact the project document.

        :param zip_archive: the zip archive to extract the project document from
        :param data_redaction_use_case: data redaction to apply to the project document
        :param json_options: json options for loading documents
        :return: the project document (redacted)
        """
        project_documents_from_zip = zip_archive.get_documents_by_collection(
            collection_name=DocumentRepo.PROJECTS_COLLECTION
        )
        project_reductions: list[Callable] = [
            data_redaction_use_case.update_user_info_in_mongodb_doc,
            data_redaction_use_case.recreate_objectid_in_mongodb_doc,
            partial(loads, json_options=json_options),
        ]
        if not self.keep_original_dates:
            project_reductions.append(data_redaction_use_case.update_creation_time_in_mongodb_doc)
        project_restored_docs = multi_map(project_documents_from_zip, *project_reductions)
        try:
            project_document: dict = next(iter(project_restored_docs))
        except StopIteration:
            raise FileNotFoundError("Project document was not found in the zip file.")

        # override project name if requested
        if self.project_name:
            project_document["name"] = self.project_name
        return project_document

    def __store_all_documents(
        self,
        project_identifier: ProjectIdentifier,
        project_document: dict,
        zip_archive: ProjectZipArchive,
        data_redaction_use_case: ImportDataRedactionUseCase,
        json_options: JSONOptions,
    ) -> None:
        """
        Stores all documents.

        :param project_document: identifier of the new project
        :param project_document: the project document to store
        :param zip_archive: the zip archive to extract the documents from
        :param data_redaction_use_case: data redaction to apply to the documents
        :param json_options: json options for loading documents
        """
        document_repo = DocumentRepo(project_identifier)
        for collection_name in zip_archive.get_collection_names():
            if collection_name in DocumentRepo.BLACKLISTED_COLLECTIONS:
                logger.warning(
                    f"The project archive contains documents for the blacklisted collection '{collection_name}'; "
                    f"skipping them."
                )
                continue
            if collection_name == DocumentRepo.PROJECTS_COLLECTION:
                # The project document has been already redacted, can be inserted directly
                document_repo.insert_documents_to_db_collection(
                    collection_name=DocumentRepo.PROJECTS_COLLECTION,
                    documents=[project_document],
                )
                continue
            documents_from_zip = zip_archive.get_documents_by_collection(collection_name=collection_name)
            media_based_id_redaction: list[Callable] = (
                [data_redaction_use_case.recreate_media_based_objectid_in_mongodb_doc]
                if collection_name in ProjectImportUseCase.COLLECTIONS_WITH_MEDIA_BASED_ID
                else []
            )
            document_reductions: list[Callable] = [
                data_redaction_use_case.update_user_info_in_mongodb_doc,
                data_redaction_use_case.recreate_objectid_based_binary_filename_in_mongodb_doc,
                data_redaction_use_case.recreate_objectid_in_mongodb_doc,
                partial(loads, json_options=json_options),
            ]
            if not self.keep_original_dates:
                document_reductions.append(data_redaction_use_case.update_creation_time_in_mongodb_doc)
            restored_docs = multi_map(documents_from_zip, *document_reductions, *media_based_id_redaction)
            document_repo.insert_documents_to_db_collection(collection_name=collection_name, documents=restored_docs)

    @staticmethod
    def _verify_signature(project_archive_path: str, signature: bytes, public_key: PublicKeyBytes) -> None:
        """
        Verifies the signature contained in the zip archive.

        :param project_archive_path: the path of the project zip archive to be imported
        :raises SignatureKeysNotFound: if the keys necessary to verify the signature cannot be located
        :raises SignatureVerificationFailed: if project verification has failed
        """
        project_data = read_file_in_chunks(filename=project_archive_path)
        SignatureUseCaseHelper.get_signature_use_case().verify(
            data=project_data,
            signature=signature,
            public_key=public_key,
        )
        logger.info("Project's signature successfully verified.")

    def _upgrade_project_data(self, project_archive_version: DataVersion) -> None:
        """
        Upgrades the data if the imported project is from a previous version.

        :param project_archive_version: data version of the imported project archive
        :raises ImportProjectUnsupportedVersionException: if the archive version is unsupported
        """
        server_data_version = DataVersion.get_current()
        logger.info(
            f"Server data version: {server_data_version.version_string} "
            f"Project archive data version: {project_archive_version.version_string}"
        )
        if project_archive_version < server_data_version:
            logger.info(
                "Upgrading imported project data from version '%s' to '%s'...",
                project_archive_version.version_string,
                server_data_version.version_string,
            )
            if self.project_id is None:
                logger.exception("Missing project ID for data upgrade.")
                raise ProjectUpgradeFailedException
            DataMigrationUseCase.upgrade_project_to_current_version(
                project_id=self.project_id, version=project_archive_version
            )
        # Note: importing project containing breaking changes is not supported
        elif project_archive_version.major > server_data_version.major:
            raise ImportProjectUnsupportedVersionException(version=project_archive_version.version_string)

    def __import_zip(  # noqa: PLR0915
        self,
        file_id: ID,
        creator_id: ID,
        tmp_folder: str,
        progress_callback: Callable[[float, str], None],
    ) -> None:
        """
        Import a project from a zip file previously uploaded to S3.

        :param file_id: ID of the uploaded zip archive file
        :param creator_id: ID of the user who is creating (importing) the project
        :param tmp_folder: Temporary local folder that can be used to store files
        :param progress_callback: callback function to report progress
        """
        session: Session = CTX_SESSION_VAR.get()
        local_zip_path = os.path.join(tmp_folder, f"{str(uuid.uuid4())}.zip")
        json_options = JSONOptions(
            uuid_representation=UuidRepresentation.STANDARD,
            datetime_representation=DatetimeRepresentation.ISO8601,
            tz_aware=True,
            tzinfo=timezone.utc,
        )

        # Download the zip file to the local filesystem
        logger.info(
            "Downloading the zip archive of operation '%s' to '%s'",
            file_id,
            local_zip_path,
        )
        progress_callback(5, "Retrieving the zip archive.")
        ProjectImportUseCase._download_import_zip(file_id=file_id, local_zip_path=local_zip_path)

        with ProjectZipArchiveWrapper(zip_file_path=local_zip_path, readonly=True) as zip_wrapper:
            # Validate
            # Note: the outer zip isn't expected to be compressed, but allow a ratio of 3 (not dangerous) anyway
            # so that a better error message will be displayed to the user if he accidentally uploaded the wrong file
            compression_ratio = zip_wrapper.validate_against_zip_bomb(allow_nested_zip=True)
            if compression_ratio > 1.0:
                logger.warning(
                    "Zip archive of operation '%s' looks compressed (ratio=%f), probably the user uploaded a bad file.",
                    file_id,
                    compression_ratio,
                )
            zip_wrapper.validate_files_structure(
                files_whitelist=[
                    zip_wrapper.PROJECT_ARCHIVE,
                    zip_wrapper.ECDSA_P384_SIGNATURE,
                    zip_wrapper.PUBLIC_KEY,
                ]
            )
            # Extract the internal project archive zip
            local_project_archive_path = zip_wrapper.extract_project_archive()
            signature = zip_wrapper.get_signature()
            public_key = zip_wrapper.get_public_key()

        self._verify_signature(
            project_archive_path=local_project_archive_path,
            signature=signature,
            public_key=public_key,
        )

        with ProjectZipArchive(zip_file_path=local_project_archive_path) as zip_archive:
            # Validate
            zip_archive.validate_against_zip_bomb()
            # Read the manifest
            manifest = zip_archive.get_manifest()
            data_redaction_use_case = ImportDataRedactionUseCase(
                objectid_replacement_min_int=int(manifest.min_id, 16),
                user_replacement_new_id=uuid.UUID(creator_id),
            )
            logger.info(
                "Extracting and processing the main project document (operation '%s')",
                file_id,
            )
            progress_callback(25, "Extracting and processing project database.")
            project_document = self.__extract_project_document(
                zip_archive=zip_archive,
                data_redaction_use_case=data_redaction_use_case,
                json_options=json_options,
            )

            self.project_id = IDToMongo.backward(project_document["_id"])
            project_identifier = ProjectIdentifier(project_id=self.project_id, workspace_id=session.workspace_id)
            logger.info(
                "The new project imported by operation '%s' is assigned id '%s'",
                file_id,
                project_identifier.project_id,
            )

            # Store all documents
            logger.info(
                "Importing documents to DB collections for new project '%s'",
                project_identifier.project_id,
            )
            self.__store_all_documents(
                project_identifier=project_identifier,
                project_document=project_document,
                zip_archive=zip_archive,
                data_redaction_use_case=data_redaction_use_case,
                json_options=json_options,
            )

            # Store the objects
            logger.info(
                "Importing binary objects for new project '%s'",
                project_identifier.project_id,
            )
            progress_callback(50, "Importing project binary files.")
            binary_storage_repo = BinaryStorageRepo(
                organization_id=session.organization_id,
                workspace_id=session.workspace_id,
                project_id=project_identifier.project_id,
            )
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []

                for object_type in BinaryObjectType:
                    if object_type == BinaryObjectType.UNDEFINED:
                        continue
                    objects_local_and_remote_paths = zip_archive.get_objects_by_type(
                        object_type=object_type,
                    )
                    objects_recreated_paths = (
                        (
                            data_redaction_use_case.recreate_objectid_in_file(lp),  # redact the file
                            data_redaction_use_case.recreate_objectid_in_url(
                                ImportDataRedactionUseCase.sanitize_extension(rp)
                            ),  # redact the path
                        )
                        for lp, rp in objects_local_and_remote_paths
                    )
                    futures.append(
                        executor.submit(
                            binary_storage_repo.store_objects_by_type,
                            object_type=object_type,
                            local_and_remote_paths=objects_recreated_paths,
                        )
                    )

                for future in futures:
                    future.result()

        # Migrate the documents and objects to the latest version
        self._upgrade_project_data(project_archive_version=DataVersion(manifest.version))

        # Register the last active model(s) to be used for online inference
        logger.info("Registering models for project '%s'", project_identifier.project_id)
        progress_callback(75, "Registering models.")
        try:
            ProjectImportUseCase._register_active_models(project_identifier=project_identifier)
        except Exception:
            logger.exception(
                "Skipping model registration for project '%s' due to an error",
                project_identifier.project_id,
            )

        metadata = {
            "project": {
                "id": project_identifier.project_id,
                "name": project_document.get("name"),
            },
        }
        publish_metadata_update(metadata)
        # publish project created kafka event
        publish_event(
            topic="project_creations",
            body={
                "workspace_id": str(project_identifier.workspace_id),
                "project_id": str(project_identifier.project_id),
            },
            key=str(project_identifier.project_id).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

        # Register project in SpiceDB
        logger.info("Creating project in SpiceDB")
        SpiceDB().create_project(
            workspace_id=str(project_identifier.workspace_id),
            project_id=str(project_identifier.project_id),
            creator=str(creator_id),
        )

        # Update the metrics
        logger.info(
            "Updating metrics for imported images and videos within project '%s'",
            project_identifier.project_id,
        )
        UpdateMetricsUseCase.update_metrics(project_identifier=project_identifier)
        logger.info("Project '%s' has been successfully imported", project_identifier.project_id)

    def import_zip(
        self,
        file_id: ID,
        creator_id: ID,
        progress_callback: Callable[[float, str], None],
    ) -> None:
        """
        Import a project from a zip file previously uploaded to S3.

        :param file_id: ID of the uploaded zip archive file
        :param creator_id: ID of the user who is creating (importing) the project
        :param progress_callback: callback function to report progress
        """
        try:
            with tempfile.TemporaryDirectory() as tmp_dir_path:
                self.__import_zip(
                    file_id=file_id,
                    creator_id=creator_id,
                    tmp_folder=tmp_dir_path,
                    progress_callback=progress_callback,
                )
        except Exception as exc:
            self.rollback_import(file_id=file_id)
            logger.exception("Failed to import project, changes have been rolled back.")
            # Exceptions that inherit from ImportProjectFailedException already have a user-friendly message,
            # so they can be re-raised as they are. Other exceptions should be converted to
            # a ImportProjectFailedException with a generic message.
            if isinstance(exc, ImportProjectFailedException):
                raise exc
            raise ImportProjectFailedException from exc
        finally:
            self._delete_import_zip(file_id=file_id)

    def rollback_import(self, file_id: ID) -> None:
        """
        Revert all the persisted changes to the database and object storage resulting from an import job.
        In practice, this method deletes all the imported MongoDB documents, S3 objects and de-registers models.

        :param file_id: ID of the import operation to rollback
        """
        session: Session = CTX_SESSION_VAR.get()
        if self.project_id is None:
            # The import failed before the project was even assigned an id, nothing to clean up
            return

        # Delete MongoDB documents
        project_identifier = ProjectIdentifier(workspace_id=session.workspace_id, project_id=self.project_id)
        try:
            DocumentRepo(project_identifier).delete_all_documents()
        except Exception:
            logger.exception(
                "Error while cleaning up MongoDB documents of project that could not be imported (upload_file_id='%s')",
                file_id,
            )
        # Delete S3 objects
        try:
            binary_storage_repo = BinaryStorageRepo(
                organization_id=session.organization_id,
                workspace_id=session.workspace_id,
                project_id=project_identifier.project_id,
            )
            for object_type in binary_storage_repo.get_object_types():
                binary_storage_repo.delete_all_objects_by_type(object_type=object_type)
        except Exception:
            logger.exception(
                "Error while cleaning up binary objects of project that could not be imported (upload_file_id='%s')",
                file_id,
            )
        # TODO CVS-130697 deregister model(s)
