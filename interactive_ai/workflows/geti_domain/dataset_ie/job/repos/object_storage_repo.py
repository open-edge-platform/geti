# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the object storage repo for dataset ie jobs
"""

import logging
import os
from collections.abc import Sequence

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from job.utils.exceptions import FileNotFoundException, MissingEnvVariables, WrongS3CredentialsProvider

logger = logging.getLogger(__name__)


class ObjectStorageRepo:
    """
    Implements the object storage repo
    """

    bucket = os.environ.get("BUCKET_NAME_TEMPORARYFILES", "")

    def __init__(self) -> None:
        s3_credentials_provider = os.environ.get("S3_CREDENTIALS_PROVIDER")
        self.client: BaseClient
        if s3_credentials_provider == "local":
            self.client = self.__authenticate_on_prem_client()
        elif s3_credentials_provider == "aws":
            self.client = self.__authenticate_saas_client()
        else:
            message = (
                "Environment variable S3_CREDENTIALS_PROVIDER should be set to either 'local' or 'aws' for S3 to work."
            )
            logger.exception(message)
            raise WrongS3CredentialsProvider(s3_credentials_provider)

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
            service_name="s3",
            region_name=os.environ.get("AWS_REGION"),
        )

    @staticmethod
    def __validate_environment_variables(required_variables: Sequence[str]) -> None:
        """
        Check if environment variables required for S3 are set.

        :param required_variables: A sequence of strings containing the names of the environment variables required.
        :raises MissingEnvVariables: If one or more environment variables are missing.
        """
        missing_env_variables = set(required_variables) - set(os.environ)
        if missing_env_variables:
            missing_variables_str = ", ".join(missing_env_variables)
            logger.exception(
                f"Environment variable(s) {missing_variables_str} were not set, but they are required for S3 to work."
            )
            raise MissingEnvVariables(missing_env_variables)

    def upload_file(self, source_path: str, key: str) -> None:
        """
        Upload a file to S3 from filesystem.

        :param source_path: path of file to upload
        :param key: key of file in object storage
        """
        with open(source_path, "rb") as file:
            self.client.upload_fileobj(Bucket=self.bucket, Key=key, Fileobj=file)

    def download_directory(self, target_path: str, key: str) -> None:
        """
        Download a directory from object storage to filesystem. The directory structure after the download will
        be the same as the structure inside S3.

        :param target_path: Target path for the directory to be downloaded to
        :param key: key of directory in bucket
        """
        response = self.client.list_objects(Bucket=self.bucket, Prefix=key)
        if "Contents" not in response:
            message = f"Failed request to get the directory at {key}. Received response: {response}"
            logger.exception(message)
            raise FileNotFoundException(message)
        file_keys = [obj["Key"] for obj in response["Contents"]]
        for file_key in file_keys:
            suffix = file_key.replace(key, "", 1)
            file_path = target_path + suffix
            self.download_file(target_path=file_path, key=file_key)

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

    def download_file(self, target_path: str, key: str) -> None:
        """
        Download a file from S3 to the filesystem

        :param target_path: path to download file into
        :param key: S3 key of file to download
        """
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        self.client.download_file(Bucket=self.bucket, Key=key, Filename=target_path)

    def delete_file(self, key: str) -> None:
        """
        Delete a file from S3 with the given key

        :param key: S3 key of file to delete
        """
        self.client.delete_object(Bucket=self.bucket, Key=key)
