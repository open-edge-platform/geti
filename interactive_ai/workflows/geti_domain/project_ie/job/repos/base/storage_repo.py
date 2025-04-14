# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines the StorageRepo base class"""

import os
from abc import ABC
from collections.abc import Sequence

import boto3
from botocore.client import BaseClient
from minio import Minio
from minio.credentials import IamAwsProvider

S3_ADDRESS = "s3.amazonaws.com"


class StorageRepo(ABC):
    """Base class for repos that interact with the S3 storage"""

    def __init__(self) -> None:
        self.minio_client: Minio
        self.boto_client: BaseClient
        s3_credentials_provider = os.environ.get("S3_CREDENTIALS_PROVIDER")
        if s3_credentials_provider == "local":
            self.minio_client, self.boto_client = self.__authenticate_on_prem_client()
        elif s3_credentials_provider == "aws":
            self.minio_client, self.boto_client = self.__authenticate_saas_client()
        else:
            raise ValueError(
                "Environment variable S3_CREDENTIALS_PROVIDER should be set to either 'local' or 'aws' for S3 to work."
            )

    @classmethod
    def __validate_environment_variables(cls, required_variables: Sequence[str]) -> None:
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

    @classmethod
    def __authenticate_on_prem_client(cls) -> tuple[Minio, BaseClient]:
        """
        Connect to the object storage from an on-prem deployment using the credentials specified in the env variables.

        :return: Tuple containing a Minio client and a boto3 client, both connected to the same host
        """
        cls.__validate_environment_variables(
            required_variables=[
                "S3_ACCESS_KEY",
                "S3_SECRET_KEY",
            ]
        )
        host_name = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        minio_client = Minio(
            endpoint=host_name,
            secure=False,
            access_key=os.environ.get("S3_ACCESS_KEY", ""),
            secret_key=os.environ.get("S3_SECRET_KEY", ""),
        )
        boto_client = boto3.client(
            service_name="s3",
            aws_access_key_id=os.environ.get("S3_ACCESS_KEY", ""),
            aws_secret_access_key=os.environ.get("S3_SECRET_KEY", ""),
            endpoint_url=f"http://{host_name}",
        )
        return minio_client, boto_client

    @classmethod
    def __authenticate_saas_client(cls) -> tuple[Minio, BaseClient]:
        """
        Connect to the object storage from a SaaS deployment using a web identity token.

        :return: Tuple containing a Minio client and a boto3 client, both connected to the same address
        """
        cls.__validate_environment_variables(
            required_variables=[
                "AWS_ROLE_ARN",
                "AWS_REGION",
                "AWS_WEB_IDENTITY_TOKEN_FILE",
            ]
        )
        minio_client = Minio(
            endpoint=S3_ADDRESS,
            region=os.environ.get("AWS_REGION"),
            credentials=IamAwsProvider(),
        )
        boto_client = boto3.client(
            service_name="s3",
            region_name=os.environ.get("AWS_REGION"),
        )
        return minio_client, boto_client
