# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from unittest.mock import patch

import mongomock
import pytest
from bson import ObjectId
from minio import Minio
from pymongo import MongoClient
from pytest_minio_mock.plugin import MockMinioClient

from migration.scripts.remove_result_media import RemoveResultMediaMigration
from migration.utils.connection import MinioStorageClient


@pytest.fixture
def fxt_result_media():
    yield {"_id": ObjectId("662c1d3460b6aa248e48148a"), "content": {"schema": "result_media"}}


@pytest.fixture
def fxt_tensor():
    yield {"_id": ObjectId("662c1d3460b6aa248e48148b"), "content": {"schema": "tensor"}}


@pytest.fixture
def minio_mock(mocker):
    def minio_mock_init(
        cls,
        *args,
        **kwargs,
    ):
        return MockMinioClient(*args, **kwargs)

    patched = mocker.patch.object(Minio, "__new__", new=minio_mock_init)
    yield patched


class TestRemoveResultMedia:
    def test_delete_result_media_from_db(self, fxt_result_media, fxt_tensor) -> None:
        """
        Verifies that only the result media documents are deleted from the metadata collection.
        """
        # Arrange
        mock_db = mongomock.MongoClient().db
        metadata_item_collection = mock_db.metadata_item
        metadata_item_collection.insert_one(fxt_result_media)
        metadata_item_collection.insert_one(fxt_tensor)

        # Act
        with patch.object(MongoClient, "get_database", return_value=mock_db):
            RemoveResultMediaMigration.delete_result_media_from_db()

        # Assert
        documents = metadata_item_collection.find()
        for doc in documents:
            assert doc["content"]["schema"] != "result_media"

    def test_delete_result_media_from_storage(self, minio_mock) -> None:
        # Arrange
        os.environ["S3_CREDENTIALS_PROVIDER"] = "aws"
        minio_client = Minio("s3.amazonaws.com")
        minio_client.make_bucket("resultmedia")
        minio_client.put_object(bucket_name="resultmedia", object_name="file1.np", data=b"a", length=1)
        minio_client.put_object(
            bucket_name="resultmedia", object_name="organizations/workspaces/projects/file2.np", data=b"b", length=1
        )

        # Act
        with patch.object(MinioStorageClient, "authenticate_saas_client", return_value=minio_client):
            RemoveResultMediaMigration.delete_result_media_from_storage()

        # Assert
        assert not minio_client.bucket_exists(bucket_name="resultmedia")
