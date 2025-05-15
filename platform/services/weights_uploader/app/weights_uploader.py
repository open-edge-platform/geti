# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

from pretrained_models.pretrained_models import MaxTriesExhausted, download_pretrained_model, retry_call

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_file(client: boto3.client, path: str, filename: str) -> None:
    """Uploads file from local_path to s3 if it does not already exist"""
    try:
        file_path = os.path.join(path, filename)
        bucket_name = "pretrainedweights"

        try:
            client.head_object(Bucket=bucket_name, Key=filename)
            logger.info(f"File {filename} already exists on S3. Skipping upload.")
            return
        except ClientError as err:
            if err.response["Error"]["Code"] != "404":
                logger.error(f"Error checking existence of {filename} on S3: {err}")
                raise err

        # Upload the file if it does not exist
        logger.info(f"Uploading file {filename} to S3")
        client.upload_file(file_path, bucket_name, filename)
        logger.info("File uploaded")
    except ClientError as err:
        logger.error(err)
        raise err


def main() -> None:
    """
    Main function of uploader for pretrained OTX weights
    """
    s3_host = "{}{}".format("http://", os.environ["S3_HOST"])
    s3_access_key = os.environ["S3_ACCESS_KEY"]
    s3_secret_key = os.environ["S3_SECRET_KEY"]
    weights_dir = os.environ["WEIGHTS_DIR"]
    weights_url = os.environ.get("WEIGHTS_URL", None)
    config_dir = os.environ.get("CONFIG_DIR", "pretrained_models")
    model_list = "pretrained_models_v2.json"
    models_list_path_v2 = os.path.join(config_dir, model_list)

    client = boto3.client(
        "s3",
        endpoint_url=s3_host,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        use_ssl=False,
    )

    upload_file(client, config_dir, model_list)

    if os.environ.get("DISABLE_WEIGHT_UPLOADING", None) is not None:
        logger.info("Downloading pretrained weights is disabled. Exiting.")
        return

    os.makedirs(weights_dir, exist_ok=True)
    with open(models_list_path_v2) as file:
        models_spec = json.load(file)

    for model in models_spec:
        initial_models = set(os.listdir(weights_dir))
        download_pretrained_model(model, weights_dir, weights_url)
        updated_models = set(os.listdir(weights_dir))
        for filename in updated_models - initial_models:
            try:
                retry_call(upload_file, client=client, path=weights_dir, filename=filename)
            except MaxTriesExhausted:
                raise


if __name__ == "__main__":
    main()
