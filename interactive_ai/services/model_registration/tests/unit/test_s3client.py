# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
import tempfile
from unittest.mock import patch

import pytest
from moto import mock_aws

from service.s3client import S3Client


@pytest.fixture
def aws_credentials():
    os.environ["S3_CREDENTIALS_PROVIDER"] = "aws"
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_SECURITY_TOKEN"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def s3_client(aws_credentials):
    with mock_aws():
        yield S3Client()


def test_init_local_credentials():
    with patch.dict(
        os.environ,
        {"S3_CREDENTIALS_PROVIDER": "local", "S3_HOST": "testhost", "S3_ACCESS_KEY": "key", "S3_SECRET_KEY": "secret"},
    ):
        client = S3Client()
        assert client.client is not None


def test_bucket_exist(s3_client):
    location = {"LocationConstraint": "eu-central-1"}
    s3_client.client.create_bucket(Bucket="test-bucket", CreateBucketConfiguration=location)
    assert s3_client.bucket_exist("test-bucket") is True
    assert s3_client.bucket_exist("not-test-bucket") is False


def test_create_bucket(s3_client):
    with patch("logging.Logger.info") as mock_logger:
        s3_client.create_bucket("my-test-bucket")
        assert s3_client.bucket_exist("my-test-bucket") is True
        mock_logger.assert_called()


def test_upload_file(s3_client):
    s3_client.client.create_bucket(Bucket="upload-bucket")
    with patch("logging.Logger.info") as mock_logger, tempfile.NamedTemporaryFile() as tmp:
        s3_client.upload_file("upload-bucket", "test.txt", tmp.name)
        mock_logger.assert_called_with("File uploaded")

    response = s3_client.client.list_objects_v2(Bucket="upload-bucket")
    assert "Contents" in response
    assert response["Contents"][0]["Key"] == "test.txt"


def test_upload_folder(s3_client):
    s3_client.client.create_bucket(Bucket="upload-bucket")
    os.mkdir("test_folder")
    with open("test_folder/file1.txt", "w") as f:
        f.write("File 1 content")
    with open("test_folder/file2.txt", "w") as f:
        f.write("File 2 content")

    with patch("logging.Logger.info") as mock_logger:
        s3_client.upload_folder("upload-bucket", "test_folder", "test_folder")
        assert mock_logger.call_count == 2
    os.remove("test_folder/file1.txt")
    os.remove("test_folder/file2.txt")
    os.rmdir("test_folder")


def test_delete_folder(s3_client):
    s3_client.client.create_bucket(Bucket="delete-bucket")
    s3_client.client.put_object(Bucket="delete-bucket", Key="folder_to_delete/file.txt", Body="data")
    s3_client.client.put_object(Bucket="delete-bucket", Key="folder_to_delete2/", Body="")

    with patch("logging.Logger.info") as mock_logger:
        s3_client.delete_folder("delete-bucket", "folder_to_delete")
        mock_logger.assert_called_with("Deleted folder `s3://delete-bucket/folder_to_delete`")

    with patch("logging.Logger.info") as mock_logger:
        s3_client.delete_folder("delete-bucket", "folder_to_delete2")
        mock_logger.assert_called_with("Deleted folder `s3://delete-bucket/folder_to_delete2`")


def test_check_folder_exists(s3_client):
    s3_client.client.create_bucket(Bucket="test-bucket")
    s3_client.client.put_object(Bucket="test-bucket", Key="good_folder/", Body="")

    assert s3_client.check_folder_exists("test-bucket", "good_folder") is True
    assert s3_client.check_folder_exists("test-bucket", "good_folder/") is True
    assert s3_client.check_folder_exists("test-bucket", "bad_folder/") is False


def test_list_folders(s3_client):
    s3_client.client.create_bucket(Bucket="list-bucket")
    folder_names = s3_client.list_folders("list-bucket")
    assert folder_names == []

    s3_client.client.put_object(Bucket="list-bucket", Key="folder1/", Body="")
    s3_client.client.put_object(Bucket="list-bucket", Key="folder1/folder3/", Body="")
    s3_client.client.put_object(Bucket="list-bucket", Key="folder2/file.txt", Body="data")

    folder_names = s3_client.list_folders("list-bucket")
    assert "folder1" in folder_names
    assert "folder2" in folder_names
