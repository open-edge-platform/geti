# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
import re
from collections.abc import Sequence

from minio import Minio
from minio.credentials import IamAwsProvider
from pymongo import MongoClient


class MongoDBConnection:
    """
    This class handles connection to the MongoDB client and fetching databases from it.
    """

    def __init__(self) -> None:
        db_name = os.getenv("MONGODB_DATABASE_NAME", "geti")
        conn_string = self._get_connection_string()
        self.client: MongoClient = MongoClient(conn_string, uuidRepresentation="standard")
        self.geti_db = self.client.get_database(db_name)

    @classmethod
    def _get_connection_string(cls) -> str:
        """Get the full URI to connect and authenticate with the MongoDB server"""

        def get_local_connection_string() -> str:
            database_address = os.environ.get("DATABASE_ADDRESS", "mongodb://localhost:27017/")
            database_username = os.environ.get("DATABASE_USERNAME", None)
            database_password = os.environ.get("DATABASE_PASSWORD", None)
            if database_username and database_password:
                add_creds_regex = r"\1" + database_username + ":" + database_password + "@"
                return re.sub(r"(mongodb://)", add_creds_regex, database_address)
            return database_address

        def get_aws_connection_string() -> str:
            database_address = os.environ.get("DATABASE_ADDRESS", None)
            if database_address is None:
                raise RuntimeError("Missing 'DATABASE_ADDRESS' env variable necessary for AWS-based auth")
            cls.check_required_env_vars(required_variables=["AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_ROLE_ARN"])
            return f"{database_address.rstrip('/')}/?authSource=%24external&authMechanism=MONGODB-AWS"

        mongodb_credentials_provider = os.environ.get("MONGODB_CREDENTIALS_PROVIDER", "local")
        match mongodb_credentials_provider:
            case "local":
                return get_local_connection_string()
            case "aws":
                return get_aws_connection_string()
            case _:
                raise ValueError(
                    f"Invalid MONGODB_CREDENTIALS_PROVIDER value for MongoDB auth: {mongodb_credentials_provider}"
                )

    @staticmethod
    def check_required_env_vars(required_variables: Sequence[str]) -> None:
        """
        Check if the given environment variables are set.

        :param required_variables: A sequence of strings containing the names of the required environment variables.
        :raises ValueError: If one or more environment variables are missing.
        """
        missing_env_variables = set(required_variables) - set(os.environ)
        if missing_env_variables:
            missing_variables_str = ", ".join(missing_env_variables)
            raise ValueError(f"Required environment variable(s) {missing_variables_str} are not set.")


class MinioStorageClient:
    """
    This class handles connection to the Minio client.
    """

    def __init__(self):
        self.client = self.get_storage_client()

    def get_storage_client(self) -> Minio:
        s3_credentials_provider = os.environ.get("S3_CREDENTIALS_PROVIDER")
        match s3_credentials_provider:
            case "local":
                return self.authenticate_on_prem_client()
            case "aws":
                return self.authenticate_saas_client()
            case _:
                raise OSError(
                    "Environment variable S3_CREDENTIALS_PROVIDER should be set to either 'local' "
                    "or 'aws' for S3 to work."
                )

    def authenticate_on_prem_client(self) -> Minio:
        """
        Authenticate a Minio client for on-premises deployment using the credentials specified in the environment
        variables.

        :return: a minio client using standard secret/access key
        """
        self.validate_environment_variables(
            required_variables=[
                "S3_ACCESS_KEY",
                "S3_SECRET_KEY",
            ]
        )
        host_name = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        return Minio(
            endpoint=host_name,
            secure=False,
            access_key=os.environ.get("S3_ACCESS_KEY", ""),
            secret_key=os.environ.get("S3_SECRET_KEY", ""),
        )

    def authenticate_saas_client(self) -> Minio:
        """
        Authenticate a Minio client for SaaS deployment using a web identity token.
          1. Validate the required environment variables
          2. Generate the credentials by authenticating to IAM, this automatically uses the defined env variables
          3. Initialize Minio client using these credentials.
        Note: In SaaS, there is no distinction between normal and pre-signed URL credentials
        """
        self.validate_environment_variables(
            required_variables=[
                "AWS_ROLE_ARN",
                "AWS_REGION",
                "AWS_WEB_IDENTITY_TOKEN_FILE",
            ]
        )
        return Minio(
            endpoint="s3.amazonaws.com",
            region=os.environ.get("AWS_REGION"),
            credentials=IamAwsProvider(),
        )

    @staticmethod
    def validate_environment_variables(required_variables: Sequence[str]) -> None:
        """
        Check if environment variables required for S3 are set.

        :param required_variables: A sequence of strings containing the names of the environment variables required.
        :raises OSError: If one or more environment variables are missing.
        """
        missing_env_variables = set(required_variables) - set(os.environ)
        if missing_env_variables:
            missing_variables_str = ", ".join(missing_env_variables)
            raise OSError(
                f"Environment variable(s) {missing_variables_str} were not set, but they are required for S3 to work."
            )
