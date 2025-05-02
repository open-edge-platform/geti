# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os

import pytest
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from iai_core_py.repos.base.mongo_connector import MongoConnector


@pytest.fixture
def fxt_aws_environment():
    old_environ = dict(os.environ)
    os.environ["MONGODB_CREDENTIALS_PROVIDER"] = "aws"
    os.environ["DATABASE_ADDRESS"] = "mongodb+srv://example.mongodb.com/"
    os.environ["AWS_WEB_IDENTITY_TOKEN_FILE"] = "path_to_token_file"
    os.environ["AWS_ROLE_ARN"] = "regular_user"
    os.environ["MONGODB_DATABASE_NAME"] = "geti-test"
    yield
    os.environ.clear()
    os.environ.update(old_environ)


@pytest.fixture
def fxt_local_environment():
    old_environ = dict(os.environ)
    os.environ["MONGODB_CREDENTIALS_PROVIDER"] = "local"
    os.environ["DATABASE_ADDRESS"] = "mongodb://10.20.30.40:8888/"
    os.environ["DATABASE_USERNAME"] = "dummy_user"
    os.environ["DATABASE_PASSWORD"] = "dummy_pass"
    os.environ["MONGODB_DATABASE_NAME"] = "geti-test"
    yield
    os.environ.clear()
    os.environ.update(old_environ)


@pytest.fixture
def fxt_clear_mongo_connector_cache():
    MongoConnector.get_database_name.cache.clear()
    MongoConnector.get_mongo_client.cache.clear()
    yield
    MongoConnector.get_database_name.cache.clear()
    MongoConnector.get_mongo_client.cache.clear()


class TestMongoConnector:
    def test_get_connection_string_aws(self, fxt_aws_environment) -> None:
        # Note: we test '_get_connection_string' instead of 'get_connection_string' to avoid the testcontainers mocking
        uri = MongoConnector._get_connection_string()

        assert uri == "mongodb+srv://example.mongodb.com/?authSource=%24external&authMechanism=MONGODB-AWS"

    def test_get_connection_string_local(self, fxt_local_environment) -> None:
        # Note: we test '_get_connection_string' instead of 'get_connection_string' to avoid the testcontainers mocking
        uri = MongoConnector._get_connection_string()

        assert uri == "mongodb://dummy_user:dummy_pass@10.20.30.40:8888/"

    def test_get_database_name(self, fxt_local_environment, fxt_clear_mongo_connector_cache) -> None:
        db_name = MongoConnector.get_database_name()

        assert db_name == "geti-test"

    def test_get_mongo_client(self, fxt_clear_mongo_connector_cache) -> None:
        client_1 = MongoConnector.get_mongo_client()
        client_2 = MongoConnector.get_mongo_client()

        assert isinstance(client_1, MongoClient)
        assert id(client_2) == id(client_2)  # ensure it is cached

    def test_get_database(self) -> None:
        db = MongoConnector.get_database()

        assert isinstance(db, Database)

    def test_get_collection(self) -> None:
        collection = MongoConnector.get_collection(collection_name="dummy_collection")

        assert isinstance(collection, Collection)
        assert collection.name == "dummy_collection"
