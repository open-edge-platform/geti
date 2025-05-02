# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Repos to fetch/store binary objects of specific projects from/to S3"""

import logging
import os
from collections.abc import Iterable, Iterator

from geti_types import ID
from iai_core.repos.storage.storage_client import BinaryObjectType
from minio.deleteobjects import DeleteObject

from .base.storage_repo import StorageRepo

logger = logging.getLogger(__name__)


class BinaryStorageRepo(StorageRepo):
    """
    Repo to manage binary objects in the S3 storage.
    It provides methods to get and store one or more objects by type.

    :param organization_id: ID of the organization of the exported/imported project
    :param workspace_id: ID of the workspace of the exported/imported project
    """

    BLACKLISTED_OBJECT_TYPES: list[BinaryObjectType] = [
        BinaryObjectType.UNDEFINED,
        BinaryObjectType.CODE_DEPLOYMENTS,
        BinaryObjectType.MLFLOW_EXPERIMENTS,
        BinaryObjectType.RESULT_MEDIA,
    ]

    def __init__(self, organization_id: ID, workspace_id: ID, project_id: ID) -> None:
        super().__init__()
        self.s3_project_root = self.__get_s3_project_root(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
        )

    @staticmethod
    def __get_s3_project_root(organization_id: ID, workspace_id: ID, project_id: ID) -> str:
        """
        Get the project root inside S3. Uses the configuration-defined OBJECT_STORAGE_BASE_PATH to determine the top
        level structure, and uses the parent entities and the project ID to generate the rest of the project root.

        :return: S3 project root as a string.
        """
        config_defined_base_path = os.environ.get("OBJECT_STORAGE_BASE_PATH", "")
        return os.path.join(
            config_defined_base_path,
            "organizations",
            str(organization_id),
            "workspaces",
            str(workspace_id),
            "projects",
            str(project_id),
        )

    @staticmethod
    def get_object_types() -> tuple[BinaryObjectType, ...]:
        """
        Get the object types that are relevant for project import/export.

        :return: Tuple of BinaryObjectType
        """
        return tuple(
            object_type
            for object_type in BinaryObjectType
            if object_type not in BinaryStorageRepo.BLACKLISTED_OBJECT_TYPES
        )

    def get_all_objects_by_type(self, object_type: BinaryObjectType, target_folder: str) -> Iterator[tuple[str, str]]:
        """
        Iterates over objects of a specific project and type. For each object, it downloads it to a temporary local
         folder, yields the local path and the remote path from the project root onward, then removes the local copy.

        :param object_type: The type of the binary object to be processed, corresponds to a bucket
        :param target_folder: Folder in the local filesystem where to download the objects from S3
        :return: An iterator yielding tuples of:
            - The local path where the object is downloaded to
            - The remote path from the project root onward where the object was downloaded from
        """
        bucket_name = object_type.bucket_name()
        if not self.minio_client.bucket_exists(bucket_name=bucket_name):
            raise FileNotFoundError(f"Bucket {bucket_name} does not exist.")
        logger.info(
            "Storing project-related files at %s from bucket %s to temporary local folder %s.",
            self.s3_project_root,
            bucket_name,
            target_folder,
        )

        objects_to_fetch = self.minio_client.list_objects(
            bucket_name=bucket_name, prefix=self.s3_project_root + "/", recursive=True
        )

        for s3_object in objects_to_fetch:
            object_name = s3_object.object_name
            object_name_from_project_root = object_name.replace(self.s3_project_root + "/", "")
            local_path = os.path.join(target_folder, object_name_from_project_root)
            try:
                self.minio_client.fget_object(
                    bucket_name=bucket_name,
                    file_path=local_path,
                    object_name=object_name,
                )
            except Exception:
                logger.exception(
                    "Failed to fetch object from location %s in bucket %s to local temporary path %s.",
                    object_name,
                    bucket_name,
                    local_path,
                )
                raise

            yield local_path, object_name_from_project_root

            if os.path.exists(local_path):
                os.remove(local_path)

    def store_objects_by_type(
        self,
        object_type: BinaryObjectType,
        local_and_remote_paths: Iterable[tuple[str, str]],
    ) -> None:
        """
        Iterates over local files and stores them at the specified remote path.

        :param object_type: The type of the binary object to be stored, corresponds to a bucket.
        :param local_and_remote_paths: An iterable of tuples containing:
            - The local path where the file can be found that should be uploaded
            - The object name where the object was found in the /binaries/ folder inside the zip file, which will be
             the target path from the project root onward inside the bucket.
        """
        if object_type in BinaryStorageRepo.BLACKLISTED_OBJECT_TYPES:
            logger.info(f"Skipping storing objects of type {object_type} because the object type is blacklisted.")
            return
        for local_path, object_name_from_project_root in local_and_remote_paths:
            bucket_name = object_type.bucket_name()

            # The rest of the structure will be the object name from the project root onward.
            object_name = os.path.join(self.s3_project_root, object_name_from_project_root)
            try:
                self.minio_client.fput_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    file_path=local_path,
                )
            except Exception:
                logger.exception(
                    "Failed to store object at %s to location %s in bucket %s.",
                    local_path,
                    object_name,
                    bucket_name,
                )
                raise

    def delete_all_objects_by_type(self, object_type: BinaryObjectType) -> None:
        """
        Delete all the remote objects of the given type under the project root folder

        :param object_type: The type of the binary object to be stored, corresponds to a bucket.
        """
        bucket_name = object_type.bucket_name()
        objects_to_delete = (
            DeleteObject(x.object_name)
            for x in self.minio_client.list_objects(
                bucket_name=bucket_name,
                prefix=self.s3_project_root + "/",
                recursive=True,
            )
        )
        errors = self.minio_client.remove_objects(bucket_name=bucket_name, delete_object_list=objects_to_delete)
        for error in errors:
            logger.error(
                "Error while deleting object of type '%s' from S3: %s",
                object_type.name,
                error,
            )
