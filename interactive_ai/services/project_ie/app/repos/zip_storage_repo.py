# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

"""Repos to fetch/store project zip archives from/to S3"""

import logging
import os

from .base.storage_repo import StorageRepo
from geti_types import ID

logger = logging.getLogger(__name__)

DOWNLOAD_URL_VALIDITY_PERIOD: int = int(os.getenv("DOWNLOAD_URL_VALIDITY_PERIOD", "900"))
logger.info(f"Pre-signed download URL will be configured to be valid for {DOWNLOAD_URL_VALIDITY_PERIOD} seconds.")


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

    def get_downloadable_archive_presigned_url(self, operation_id: ID, download_file_name: str = "project.zip") -> str:
        """
        Get a pre-signed URL to download the project archive for the given export operation.

        :param operation_id: ID of the export operation that created the archive
        :param download_file_name: Name assigned to the file downloaded through the pre-signed URL
        """
        zip_s3_path = self.__get_download_zip_path(operation_id=operation_id)
        return self.boto_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": zip_s3_path,
                "ResponseContentDisposition": f'attachment; filename="{download_file_name}"',
            },
            ExpiresIn=DOWNLOAD_URL_VALIDITY_PERIOD,
        )

    def create_multipart_upload(self, operation_id: ID) -> str:
        """
        Create a multi-upload file.

        :param operation_id: id of the upload operation
        :return: id of the boto3 multipart upload operation - note: this is not an OTX ID but a s3 multipart upload id.
        """
        s3_response = self.boto_client.create_multipart_upload(
            Bucket=self.bucket_name,
            Key=self.__get_upload_zip_path(operation_id=operation_id),
        )
        upload_id = s3_response.get("UploadId", None)
        if upload_id is None:
            raise ValueError("Did not receive upload ID after creating multipart upload.")
        logger.info(f"Created multipart upload for operation id {operation_id}, with multipart upload id {upload_id}.")
        return upload_id

    def upload_part_to_file(self, operation_id: ID, upload_id: str, part_number: int, data: bytes) -> str:
        """
        Append data to file with specified operation id

        :param operation_id: ID of the upload operation
        :param data: bytes to append to the file
        :param upload_id: id of the boto3 multipart upload operation, not an OTX ID but s3-specific multipart upload ID
        :param part_number: part number of the file
        :return: etag of uploaded part.
        """
        s3_response = self.boto_client.upload_part(
            Body=data,
            Bucket=self.bucket_name,
            Key=self.__get_upload_zip_path(operation_id=operation_id),
            PartNumber=part_number,
            UploadId=upload_id,
        )
        etag = s3_response.get("ETag", None)
        if etag is None:
            raise ValueError("Did not receive etag after appending part to multipart upload")
        logger.debug(f"Uploaded part to file for operation ID {operation_id}.")
        return etag

    def complete_multipart_upload(self, operation_id: ID, upload_id: str, parts: list[dict]) -> None:
        """
        Complete multipart upload of different parts

        :param operation_id: ID of the file
        :param upload_id: ID of the boto3 upload operation
        :param parts: list of metadata for all parts, containing the etag and part number for every uploaded part.
        """
        self.boto_client.complete_multipart_upload(
            Bucket=self.bucket_name,
            Key=self.__get_upload_zip_path(operation_id=operation_id),
            UploadId=upload_id,
            MultipartUpload={
                "Parts": [
                    {
                        "ETag": part["ETag"],
                        "PartNumber": part["PartNumber"],
                    }
                    for part in parts
                ],
            },
        )
        logger.info(f"Completed upload with operation ID {operation_id}.")
