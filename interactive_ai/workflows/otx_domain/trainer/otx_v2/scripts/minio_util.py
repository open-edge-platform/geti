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

import logging
import os
import traceback

import requests
from minio import Minio
from minio.credentials import IamAwsProvider
from minio.error import S3Error

logger = logging.getLogger("mlflow_job")


def download_file_from_s3(bucket_name, object_name, file_path, endpoint):  # noqa: ANN001, ANN201, D103
    # Initialize the Minio client
    s3_credentials_provider = os.environ.get("S3_CREDENTIALS_PROVIDER")
    if s3_credentials_provider == "local":
        client = Minio(
            endpoint=endpoint,
            access_key=os.environ.get("S3_ACCESS_KEY", ""),
            secret_key=os.environ.get("S3_SECRET_KEY", ""),
            secure=False,
        )
        presigned_urls_client = Minio(
            endpoint=endpoint,
            access_key=os.environ.get("S3_PRESIGNED_URL_ACCESS_KEY", ""),
            secret_key=os.environ.get("S3_PRESIGNED_URL_SECRET_KEY", ""),
            secure=False,
        )
    elif s3_credentials_provider == "aws":
        client = Minio(
            endpoint="s3.amazonaws.com",
            region=os.environ.get("AWS_REGION"),
            credentials=IamAwsProvider(),
        )
        presigned_urls_client = Minio(
            endpoint="s3.amazonaws.com",
            region=os.environ.get("AWS_REGION"),
            credentials=IamAwsProvider(),
        )

    objects = client.list_objects(bucket_name, recursive=True)
    for object in objects:
        logger.info(object)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        # Download the file from the S3 bucket
        client.fget_object(bucket_name, object_name, file_path)
        print(f"File '{object_name}' downloaded successfully to '{file_path}'")
    except S3Error:
        logger.warning(f"{traceback.print_exc()}")
        logger.warning("Trying to get object using presigned URL")
        url = presigned_urls_client.presigned_get_object(bucket_name, object_name)
        try:
            resp = requests.get(url, timeout=600)
            if resp.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=512):
                        if chunk:
                            f.write(chunk)
                logger.info(f"File '{object_name}' downloaded successfully to '{file_path}' using presigned URL")
        except Exception:
            print(f"{traceback.print_exc()}")
            raise


# Example usage
if __name__ == "__main__":
    bucket_name = "pretrainedweights"
    object_name = "pretrained_models.json"
    file_path = "./temp_downloaded.obj"
    endpoint = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")

    download_file_from_s3(bucket_name, object_name, file_path, endpoint)
