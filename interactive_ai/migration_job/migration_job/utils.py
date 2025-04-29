# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
import re
from collections.abc import Sequence

from pymongo import MongoClient


def create_mongo_client() -> MongoClient:
    """Returns a Mongo client instance"""
    conn_string = _get_connection_string()
    return MongoClient(conn_string, uuidRepresentation="standard")


def _get_connection_string() -> str:
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
        check_required_env_vars(required_variables=["AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_ROLE_ARN"])
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
