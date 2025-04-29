"""A script for creating a S3 bucket."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

    def __init__(self, endpoint: str, access_key: str, secret_key: str) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            use_ssl=False,
        )

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
            raise err


def main():  # noqa: ANN201
    """The script's entry point.

    :raise EnvironmentError: If any of the required environment variables is not set.
    """
    try:
        s3_address = os.environ["S3_ADDRESS"]
        s3_access_key = os.environ["S3_ACCESS_KEY"]
        s3_secret_key = os.environ["S3_SECRET_KEY"]
        s3_bucket = os.environ["S3_BUCKET"]
    except KeyError as err:
        raise OSError("The required environment variables are not set correctly.") from err

    logger.info(f"Creating bucket {repr(s3_bucket)} at {repr(s3_address)}.")

    s3_client = S3Client(
        endpoint=s3_address,
        access_key=s3_access_key,
        secret_key=s3_secret_key,
    )
    bucket_names = s3_bucket.split(";")
    for bucket_name in bucket_names:
        s3_client.create_bucket(bucket_name=bucket_name)
