# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from unittest.mock import patch

import pytest
from minio import Minio
from minio.commonconfig import CopySource
from pytest_minio_mock.plugin import MockMinioClient

from migration.scripts.sanitize_media_binary_extension import SanitizeMediaBinaryExtensionMigration
from migration.utils.connection import MinioStorageClient

DUMMY_ORGANIZATION_ID = "11fdb5ad-8e0d-4301-b22b-06589beef658"
DUMMY_WORKSPACE_ID = "11fdb5ad-8e0d-4301-b22b-06589beef658"
DUMMY_PROJECT_ID = "66a0faf070cdf6d0b2ec5f93"


class MyMockMinioClient(MockMinioClient):
    """Extends MockMinioClient with method 'copy_object'"""

    def copy_object(self, bucket_name: str, object_name: str, source: CopySource) -> None:
        # create a new object with empty data
        self.put_object(bucket_name=bucket_name, object_name=object_name, data=b"", length=0)


@pytest.fixture
def minio_mock(mocker):
    def minio_mock_init(
        cls,
        *args,
        **kwargs,
    ):
        return MyMockMinioClient(*args, **kwargs)

    patched = mocker.patch.object(Minio, "__new__", new=minio_mock_init)
    yield patched


class TestSanitizeMediaBinaryExtensionMigration:
    def test_upgrade_non_project_data(self, minio_mock) -> None:
        # Arrange
        os.environ["S3_CREDENTIALS_PROVIDER"] = "aws"
        minio_client = Minio("s3.amazonaws.com")
        self._populate_storage(minio_client)

        # Act
        with (
            patch.object(MinioStorageClient, "authenticate_saas_client", return_value=minio_client),
        ):
            SanitizeMediaBinaryExtensionMigration.upgrade_non_project_data()

        # Assert
        image_objects = list(minio_client.list_objects(bucket_name="images", recursive=True))
        assert len(image_objects) == 3
        assert all(obj.object_name.lower().endswith((".jpg", ".png")) for obj in image_objects)
        video_objects = list(minio_client.list_objects(bucket_name="videos", recursive=True))
        assert len(video_objects) == 3
        assert all(obj.object_name.lower().endswith((".mp4",)) for obj in video_objects)

    @staticmethod
    def _populate_storage(minio_client):
        minio_client.make_bucket("images")
        minio_client.make_bucket("videos")
        minio_client.put_object(bucket_name="images", object_name="file1.JPG", data=b"a", length=1)
        minio_client.put_object(bucket_name="images", object_name="file2.jpg", data=b"b", length=1)
        minio_client.put_object(bucket_name="videos", object_name="file3.MP4", data=b"c", length=1)
        minio_client.put_object(bucket_name="videos", object_name="file4.mp4", data=b"d", length=1)

        project_prefix = (
            f"/organizations/{DUMMY_ORGANIZATION_ID}/workspaces/{DUMMY_WORKSPACE_ID}/projects/{DUMMY_PROJECT_ID}"
        )
        minio_client.put_object(bucket_name="images", object_name=f"{project_prefix}/file5.PNG", data=b"e", length=1)
        minio_client.put_object(bucket_name="videos", object_name=f"{project_prefix}/file6.MP4", data=b"f", length=1)
