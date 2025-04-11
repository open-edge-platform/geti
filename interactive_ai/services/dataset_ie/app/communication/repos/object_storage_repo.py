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
"""
This module implements the object storage data repo
"""

import abc
import logging
import os
from collections.abc import Sequence

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

from application.data_repo_interface import IObjectDataRepo

from geti_types import CTX_SESSION_VAR, ID, Session

logger = logging.getLogger(__name__)


class ObjectDataRepo(IObjectDataRepo, metaclass=abc.ABCMeta):
    """
    Implements the data repo for the dataset IE MS
    """

    bucket: str = os.environ.get("BUCKET_NAME_TEMPORARYFILES", "temporaryfiles")
    zipped_file_name: str = "dataset.zip"

    def __init__(self) -> None:
        session: Session = CTX_SESSION_VAR.get()
        self.organization_id = session.organization_id
        self.workspace_id = session.workspace_id
        s3_credentials_provider = os.environ.get("S3_CREDENTIALS_PROVIDER")
        self.client: BaseClient
        if s3_credentials_provider == "local":
            self.client = self.__authenticate_on_prem_client()
        elif s3_credentials_provider == "aws":
            self.client = self.__authenticate_saas_client()
        else:
            raise ValueError(
                "Environment variable S3_CREDENTIALS_PROVIDER should be set to either 'local' or 'aws' for S3 to work."
            )

    def __authenticate_on_prem_client(self) -> BaseClient:
        """
        Authenticate a boto3 client for on-premises deployment using the credentials specified in the environment
        variables.

        :return: boto3 client with authentication to connect to seaweedFS
        """
        self.__validate_environment_variables(required_variables=["S3_ACCESS_KEY", "S3_SECRET_KEY"])
        host_name = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        access_key = os.environ.get("S3_ACCESS_KEY", "")
        secret_key = os.environ.get("S3_SECRET_KEY", "")
        return boto3.client(
            service_name="s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=f"http://{host_name}",
        )

    def __authenticate_saas_client(self) -> BaseClient:
        """
        Authenticate a boto3 client for SaaS deployment using a web identity token. As stated in boto3 documentation,
        if you have an IAM role configured, there's no explicit configuration you need to set in Boto3 to use these
        credentials. Boto3 will automatically use IAM role credentials if it does not find credentials in any of the
        other places.

        :return: boto3 client with authentication to connect to AWS S3
        """
        self.__validate_environment_variables(
            required_variables=[
                "AWS_ROLE_ARN",
                "AWS_REGION",
                "AWS_WEB_IDENTITY_TOKEN_FILE",
            ]
        )
        return boto3.client(
            service_name="s3", region_name=os.environ.get("AWS_REGION"), config=Config(signature_version="s3v4")
        )

    def save_file(self, id_: ID, data: bytes) -> None:
        """
        Save data to object storage with specified id

        :param id_: id of the file
        :param data: bytes to write to the file
        """
        response = self.client.put_object(
            Body=data,
            Bucket=self.bucket,
            Key=f"{self.get_import_directory_path(import_id=id_)}/{self.zipped_file_name}",
            ContentType="application/octet-stream",
        )
        logger.info(f"Object added to object storage with response {response}")

    def create_multi_upload_file(self, id_: ID) -> str:
        """
        Create a multi-upload file

        :param id_: id of the file
        :return: id of the boto3 upload operation
        """
        upload_id = self.client.create_multipart_upload(
            Bucket=self.bucket,
            Key=f"{self.get_import_directory_path(import_id=id_)}/{self.zipped_file_name}",
        )["UploadId"]
        logger.info(f"Create multi upload file with id {upload_id}")
        return upload_id

    def upload_part_to_file(self, id_: ID, upload_id: str, part_number: int, data: bytes) -> str:
        """
        Append data to file with specified id

        :param id_: id of the file
        :param data: bytes to append to the file
        :param upload_id: id of the boto3 upload operation
        :param part_number: part number of the file
        :return: etag of uploaded part.
        """
        response = self.client.upload_part(
            Body=data,
            Bucket=self.bucket,
            Key=f"{self.get_import_directory_path(import_id=id_)}/{self.zipped_file_name}",
            PartNumber=part_number,
            UploadId=upload_id,
        )
        logger.info(f"Uploaded part to file with id {id_} with response {response}")
        return response["ETag"]

    def complete_file_upload(self, id_: ID, upload_id: str, parts: list[dict]) -> None:
        """
        Complete multipart upload of different parts

        :param id_: ID of the file
        :param upload_id: ID of the boto3 upload operation
        :param parts: list of metadata parts
        """
        response = self.client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=f"{self.get_import_directory_path(import_id=id_)}/{self.zipped_file_name}",
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
        logger.info(f"Completed upload to file with id {id_} with response {response}")

    def abort_multi_part_upload(self, id_: ID, upload_id: str) -> None:
        """
        Abort multi-part upload and free up space

        :param id_: ID of the upload to abort
        :param upload_id: upload id of the upload to abort
        """
        response = self.client.abort_multipart_upload(
            Bucket=self.bucket,
            Key=f"{self.get_import_directory_path(id_)}/{self.zipped_file_name}",
            UploadId=upload_id,
        )
        logger.info(f"Aborted upload to file with id {id_} with response {response}")

    def delete_by_id(self, id_: ID) -> None:
        """
        Delete data for a given id

        :param id_: id of data to delete
        """
        directory_key = f"{self.get_import_directory_path(id_)}"
        self.delete_directory(key=directory_key)

    def delete_directory(self, key: str) -> None:
        """
        Delete a directory contents from S3 storage by key

        :param key: the key of the directory to delete
        """
        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=key + "/")
        if "Contents" not in response:
            logger.info(f"No objects found in directory {key}. Skipping deletion.")
            try:
                self.client.delete_object(Bucket=self.bucket, Key=key)
            except ClientError:
                logger.warning(f"Cannot delete empty folder({key}) from S3 bucket({self.bucket})")
            return

        objects_to_delete = []
        for obj in response["Contents"]:
            objects_to_delete.append({"Key": obj["Key"]})

        try:
            response = self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": objects_to_delete})
        except ClientError:
            logger.warning(f"Cannot delete objects in a folder({key}) from S3 bucket({self.bucket})")

    def get_zipped_dataset_presigned_url(self, id_: ID, filename: str) -> str:
        """
        Obtain a presigned URL with a download for the zipped dataset in object storage

        :param id_: ID of the dataset to be downloaded
        :param filename: Filename to set for the file at the presigned URL
        """
        file_key = f"{self.get_export_directory_path(export_id=id_)}/{self.zipped_file_name}"
        try:
            return self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": file_key,
                    "ResponseContentDisposition": f'attachment; filename="{filename}"',
                },
                ExpiresIn=24 * 60 * 60,
            )
        except ClientError as e:
            logger.error(e)
            raise FileNotFoundError

    @staticmethod
    def __validate_environment_variables(required_variables: Sequence[str]) -> None:
        """
        Check if environment variables required for S3 are set.

        :param required_variables: A sequence of strings containing the names of the environment variables required.
        :raises ValueError: If one or more environment variables are missing.
        """
        missing_env_variables = set(required_variables) - set(os.environ)
        if missing_env_variables:
            missing_variables_str = ", ".join(missing_env_variables)
            raise ValueError(
                f"Environment variable(s) {missing_variables_str} were not set, but they are required for S3 to work."
            )

    def get_import_directory_path(self, import_id: ID) -> str:
        """
        Get the directory structure inside S3 where the import-related files for an organization and workspaces
        are stored.

        :param import_id: ID of the import operation
        :return: Directory structure inside S3 where the import-related files are stored
        """
        return os.path.join(
            os.environ.get("OBJECT_STORAGE_BASE_PATH", ""),
            "organizations",
            str(self.organization_id),
            "workspaces",
            str(self.workspace_id),
            "imports",
            import_id,
        )

    def get_export_directory_path(self, export_id: ID) -> str:
        """
        Get the directory structure inside S3 where the export-related files for an organization and workspaces
        are stored.

        :param export_id: ID of the export operation
        :return: Directory structure inside S3 where the export-related files are stored
        """
        return os.path.join(
            os.environ.get("OBJECT_STORAGE_BASE_PATH", ""),
            "organizations",
            str(self.organization_id),
            "workspaces",
            str(self.workspace_id),
            "exports",
            export_id,
        )
