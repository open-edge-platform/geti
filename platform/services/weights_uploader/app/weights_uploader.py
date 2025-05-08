# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main function of uploader for pretrained OTX weights
    """
    s3_host = "{}{}".format("http://", os.environ["S3_HOST"])
    s3_access_key = os.environ["S3_ACCESS_KEY"]
    s3_secret_key = os.environ["S3_SECRET_KEY"]
    weights_dir = os.environ["WEIGHTS_DIR"]
    client = boto3.client(
        "s3",
        endpoint_url=s3_host,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        use_ssl=False,
    )
    for filename in os.listdir(weights_dir):
        """Uploads file from local_path to s3"""
        try:
            file_path = os.path.join(weights_dir, filename)
            logger.info(file_path)
            client.upload_file(file_path, "pretrainedweights", filename)
            logger.info("File uploaded")
        except ClientError as err:
            logger.error(err)
            raise err


if __name__ == "__main__":
    main()
