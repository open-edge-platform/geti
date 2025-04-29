# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Centralized management of MongoDB clients and connections"""

import os
import re
from threading import Lock

from cachetools import TTLCache, cached
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from sc_sdk.utils.environment import check_required_env_vars

DEFAULT_DATABASE_NAME = "geti"
MONGO_CLIENT_CACHE_TTL = int(os.environ.get("MONGO_CLIENT_CACHE_TTL", 3600))


class MongoConnector:
    """
    MongoConnector manages connection and authentication with MongoDB servers.

    The type of connection depends on the variable 'MONGODB_CREDENTIALS_PROVIDER', which supports both
    locally deployed MongoDB clusters ("local") or MongoDB Atlas with IAM authentication ("aws").

    AWS-based authentication requires the following environment variables:
      - AWS_WEB_IDENTITY_TOKEN_FILE
      - AWS_ROLE_ARN

    The database name shall be configured through the 'MONGODB_DATABASE_NAME' environment variable.
    """

    @staticmethod
    def get_connection_string() -> str:
        """Get the full URI to connect and authenticate with the MongoDB server"""
        # Note: this indirection layer exists to facilitate testing
        return MongoConnector._get_connection_string()

    @staticmethod
    def _get_connection_string() -> str:
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

    @staticmethod
    @cached(cache={})
    def get_database_name() -> str:
        """Get the name of the MongoDB database (i.e. the container of the collections)"""
        return os.environ.get("MONGODB_DATABASE_NAME", DEFAULT_DATABASE_NAME)

    @staticmethod
    @cached(cache=TTLCache(maxsize=1, ttl=MONGO_CLIENT_CACHE_TTL), lock=Lock())
    def get_mongo_client() -> MongoClient:
        """Get or create a pymongo.MongoClient"""
        conn_string = MongoConnector.get_connection_string()
        return MongoClient(conn_string, uuidRepresentation="standard")

    @staticmethod
    def get_database() -> Database:
        """Get the pymongo.Database"""
        db_name = MongoConnector.get_database_name()
        return MongoConnector.get_mongo_client().get_database(name=db_name)

    @staticmethod
    def get_collection(collection_name: str) -> Collection:
        """Get the pymongo.Collection for the given collection name"""
        return MongoConnector.get_database().get_collection(name=collection_name)
