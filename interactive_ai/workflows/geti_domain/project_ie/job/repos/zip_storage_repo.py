# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Repos to fetch/store project zip archives from/to S3"""

import logging
import os

from geti_types import ID

from .base.storage_repo import StorageRepo

logger = logging.getLogger(__name__)


class ZipStorageRepo(StorageRepo):
    """
    Repo to manage project zip archives in the S3 object storage.
    It provides methods to upload archives (with TUS), download them and generate pre-signed URLs.

    :param organization_id: ID of the organization of the exported/imported project
    :param workspace_id: ID of the workspace of the exported/imported project
    """

    bucket_name: str = os.environ.get("BUCKET_NAME_TEMPORARYFILES", "temporaryfiles")
    zipped_file_name: str = "project.zip"

    def __init__(self, organization_id: ID, workspace_id: ID) -> None:
        super().__init__()
        self.s3_workspace_root = self.__get_s3_workspace_root(
            organization_id=organization_id, workspace_id=workspace_id
        )

    @staticmethod
    def __get_s3_workspace_root(organization_id: ID, workspace_id: ID) -> str:
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
        )

    def __get_upload_zip_path(self, operation_id: ID) -> str:
        """
        Get the S3 path where the project zip archive (to import) are uploaded by the user

        :param operation_id: Operation ID for the upload operation
        :return: Path for the file to be uploaded to in S3.
        """
        return os.path.join(self.s3_workspace_root, "uploads", operation_id, self.zipped_file_name)

    def __get_download_zip_path(self, operation_id: ID) -> str:
        """
        Get the S3 path where the (exported) project zip archive can be downloaded by the user

        :param operation_id: Operation ID for the upload operation
        :return: Path for the file to be uploaded to in S3.
        """
        return os.path.join(self.s3_workspace_root, "downloads", operation_id, self.zipped_file_name)

    def upload_downloadable_archive(self, operation_id: ID, zip_local_path: str) -> None:
        """
        Upload a (exported) project archive to S3 so that it can be later downloaded by the user.

        :param operation_id: ID of the export operation
        :param zip_local_path: Path of the project zip archive in the local filesystem
        """
        zip_s3_path = self.__get_download_zip_path(operation_id=operation_id)
        with open(zip_local_path, "rb") as fp:
            self.boto_client.upload_fileobj(Bucket=self.bucket_name, Key=zip_s3_path, Fileobj=fp)

    def download_import_zip(self, operation_id: ID, target_local_path: str) -> None:
        """
        Download an uploaded zip file to local storage

        :param operation_id: Operation ID identifying the upload/import operation
        :param target_local_path: Target path for the file to be downloaded to
        """
        if os.path.exists(target_local_path):
            raise FileExistsError(
                f"Cannot download a file to {target_local_path} because a file already exists at this location."
            )
        self.boto_client.download_file(
            Bucket=self.bucket_name,
            Key=self.__get_upload_zip_path(operation_id=operation_id),
            Filename=target_local_path,
        )

    def delete_import_zip(self, operation_id: ID) -> None:
        """
        Delete the uploaded zip file from the object storage

        :param operation_id: Operation ID identifying the upload/import operation
        """
        self.boto_client.delete_object(
            Bucket=self.bucket_name,
            Key=self.__get_upload_zip_path(operation_id=operation_id),
        )
