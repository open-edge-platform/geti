# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

REMOTE_S3_SERVER_ADDR = os.environ.get(
    "REMOTE_S3_SERVER_ADDR", "http://s3.toolbox.iotg.sclab.intel.com"
)
REMOTE_S3_TEST_BUCKET = os.environ.get("REMOTE_S3_TEST_BUCKET", "test")
REMOTE_S3_TEST_DATA_PREFIX = os.environ.get(
    "REMOTE_S3_TEST_PATH_PREFIX", "data/iai-e2e"
)

logger = logging.getLogger(__name__)


class RemoteFileNotFound(FileNotFoundError):
    """Exception raised when the requested file is not found in the remote archive"""


class RemoteFileNotAccessible(RuntimeError):
    """Exception raised when the requested file is not accessible in the remote archive due to permissions"""


def list_files_in_remote_archive(remote_dir_path: Path) -> list[str]:
    """
    List files in the remote S3 archive.

    :param remote_dir_path: Path to the directory in the remote archive, relative to the testing base directory
    :return: List of file names in the remote directory
    """
    s3_client = boto3.client("s3", endpoint_url=REMOTE_S3_SERVER_ADDR)

    # List files in the remote directory
    dir_key = str(REMOTE_S3_TEST_DATA_PREFIX / remote_dir_path) + "/"

    logger.info(f"Listing objects in '{dir_key}'")
    response = s3_client.list_objects_v2(Bucket=REMOTE_S3_TEST_BUCKET, Prefix=dir_key)

    return [obj["Key"] for obj in response.get("Contents", [])]


def download_file_from_remote_archive(
    remote_file_path: Path, local_file_path: Path
) -> None:
    """
    Download the requested file from the remote S3 archive.

    :param remote_file_path: Path to the file in the remote archive, relative to the testing base directory
    :param local_file_path: Path to save the file locally
    :raises RemoteFileNotFound: If the requested file is not found in the remote archive
    :raises RemoteFileNotAccessible: If the requested file is not accessible in the remote archive due to permissions
    :raises RuntimeError: If the file download fails for any other reason
    """
    s3_client = boto3.client("s3", endpoint_url=REMOTE_S3_SERVER_ADDR)

    # Download the file
    file_key = REMOTE_S3_TEST_DATA_PREFIX / remote_file_path

    try:
        s3_client.download_file(
            REMOTE_S3_TEST_BUCKET, str(file_key), str(local_file_path)
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "404":
            raise RemoteFileNotFound(
                f"File not found in remote archive: {file_key}"
            ) from exc
        if exc.response["Error"]["Code"] == "403":
            raise RemoteFileNotAccessible(
                f"File not accessible in remote archive: {file_key}"
            ) from exc
        raise RuntimeError(
            f"Failed to download file from remote archive: {file_key}"
        ) from exc
