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

import logging
import os
import sys

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Client:
    """
    This class is responsible for initializing S3 client
    """

    def __init__(self) -> None:
        if os.environ.get("S3_CREDENTIALS_PROVIDER", "local") == "local":
            try:
                s3_host = "{}{}".format("http://", os.environ["S3_HOST"])
                s3_access_key = os.environ["S3_ACCESS_KEY"]
                s3_secret_key = os.environ["S3_SECRET_KEY"]
            except KeyError as err:
                raise OSError("The required environment variables are not set correctly.") from err
            self.client = boto3.client(
                "s3",
                endpoint_url=s3_host,
                aws_access_key_id=s3_access_key,
                aws_secret_access_key=s3_secret_key,
                use_ssl=False,
            )
        elif os.environ.get("AWS_DEFAULT_REGION") is not None:
            self.client = boto3.client("s3", region_name=os.environ["AWS_DEFAULT_REGION"])
        else:
            self.client = boto3.client("s3")

    def bucket_exist(self, bucket_name: str) -> bool:
        """Check if an S3 bucket exist in the default region
        :param bucket_name: Name of the bucket to check.
        """
        try:
            self.client.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {repr(bucket_name)} already exists")
            return True
        except ClientError as err:
            if err.response["Error"]["Code"] == "404":
                return False
            if err.response["Error"]["Code"] == "403":
                logger.info(f"You do not have permission to access {repr(bucket_name)} bucket")
            raise err

    def create_bucket(self, bucket_name: str) -> None:
        """Create an S3 bucket in the default region.
        :param bucket_name: Name of the bucket to create.
        """
        try:
            if not self.bucket_exist(bucket_name=bucket_name):
                response = self.client.create_bucket(Bucket=bucket_name)
                logger.info(response)
        except ClientError as err:
            logger.error(err)
            raise err

    def download_file(self, bucket_name: str, object_key: str, local_path: str):  # noqa: ANN201
        """Download file from s3 to local path"""
        try:
            self.client.download_file(bucket_name, object_key, local_path)
            logger.info("File downloaded")
        except ClientError as err:
            logger.error(err)
            raise err

    def upload_file(self, bucket_name: str, object_key: str, local_path: str):  # noqa: ANN201
        """Uploads file from local_path to s3"""
        try:
            self.client.upload_file(local_path, bucket_name, object_key)
            logger.info("File uploaded")
        except ClientError as err:
            logger.error(err)
            raise err

    def upload_folder(self, bucket_name: str, object_key: str, local_folder_path: str):  # noqa: ANN201
        """Uploads local folder to s3"""
        try:
            for root, _dirs, files in os.walk(local_folder_path):
                for file in files:
                    local_path = os.path.join(root, file)
                    s3_path = os.path.join(object_key, os.path.relpath(local_path, local_folder_path))
                    logger.info(f"Uploading {local_path} to s3://{bucket_name}/{s3_path}")
                    self.client.upload_file(local_path, bucket_name, s3_path)
        except ClientError as err:
            logger.error(err)
            raise err

    def delete_folder(self, bucket_name: str, object_key: str):  # noqa: ANN201
        """Deletes folder on s3"""
        try:
            objects = self.client.list_objects_v2(Bucket=bucket_name, Prefix=object_key + "/")
        except ClientError as err:
            logger.error(err)
            raise err
        has_content = "Contents" in objects
        folder_name = f"s3://{bucket_name}/{object_key}"
        if has_content:
            delete_keys = [{"Key": obj["Key"]} for obj in objects["Contents"]]
            try:
                self.client.delete_objects(Bucket=bucket_name, Delete={"Objects": delete_keys})
                logger.info(f"Deleted folder `{folder_name}`")
            except ClientError as err:
                logger.error(err)
                raise err
        else:
            try:
                self.client.delete_object(Bucket=bucket_name, Key=object_key)
            except ClientError as err:
                logger.error(err)
                raise err
            logger.info(f"Deleted empty folder `{folder_name}`.")

    def check_folder_exists(self, bucket_name: str, object_key: str) -> bool:
        """
        Check if a folder with name `object_key` exists on S3, and it is not empty

        :param bucket_name: Name of the bucket to search in
        :param object_key: Name of the folder to check for
        :return: True if folder with name `object_key` exists on S3 and it is not empty, false otherwise
        """
        if not object_key.endswith("/"):
            object_key += "/"
        try:
            resp = self.client.list_objects_v2(Bucket=bucket_name, Prefix=object_key, MaxKeys=1)
        except ClientError as err:
            logger.error(err)
            raise err
        exists = "Contents" in resp
        if exists:
            logger.info(f"Found folder `{object_key}` on s3")
        else:
            logger.info(f"Folder `{object_key}` does not exist or is empty")
        return exists

    def list_folders(self, bucket_name: str) -> list[str]:
        """
        Return a list of names of all folders in the bucket. Note that this only returns
        top-level folder names

        :param bucket_name: Name of the bucket to search in
        :return: List of folder names which exist in the bucket. Empty folders are
            also included.
        """
        try:
            resp = self.client.list_objects_v2(Bucket=bucket_name)
        except ClientError as err:
            logger.error(err)
            raise err
        if "Contents" not in resp:
            return []
        folder_names: list[str] = []
        for object in resp["Contents"]:
            split_name = object["Key"].split("/")
            if len(split_name) == 2:
                folder_names.append(split_name[0])
        return folder_names
