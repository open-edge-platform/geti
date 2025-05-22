# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from weights_uploader import main


# Mock the environment variables
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("S3_HOST", "fake_host")
    monkeypatch.setenv("S3_ACCESS_KEY", "fake_access_key")
    monkeypatch.setenv("S3_SECRET_KEY", "fake_secret_key")
    monkeypatch.setenv("WEIGHTS_DIR", "/weights")


mock_file_content = '[{"model": "model1", "url": "http://example.com/model1", "target": "/path/to/target1"}, {"model": "model2", "url": "http://example.com/model2", "target": "/path/to/target2"}]'  # Mock JSON content


def test_main_success():
    with (
        patch("boto3.client") as boto3_client_mock,
        patch("os.listdir") as listdir_mock,
        patch("os.path.join") as join_mock,
        patch("os.makedirs") as makedirs_mock,
        patch("weights_uploader.logger") as logger_mock,
        patch("builtins.open", new_callable=MagicMock) as open_mock,
        patch("json.load") as json_load_mock,
        patch("weights_uploader.download_pretrained_model") as download_pretrained_model_mock,
    ):
        listdir_mock.return_value = ["weight1", "weight2"]
        join_mock.side_effect = lambda x, y: f"{x}/{y}"
        makedirs_mock.return_value = None
        client_instance_mock = MagicMock()
        client_instance_mock.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "head_object")

        boto3_client_mock.return_value = client_instance_mock
        open_mock.return_value.__enter__.return_value = MagicMock()
        json_load_mock.return_value = json.loads(mock_file_content)
        download_pretrained_model_mock.return_value = None  # Mock the download function

        main()

        assert boto3_client_mock.called
        assert client_instance_mock.upload_file.call_count == 1
        logger_mock.info.assert_called()
        logger_mock.error.assert_not_called()
        download_pretrained_model_mock.assert_called()


def test_main_upload_error():
    with (
        patch("boto3.client") as boto3_client_mock,
        patch("os.listdir") as listdir_mock,
        patch("os.path.join") as join_mock,
        patch("os.makedirs") as makedirs_mock,
        patch("json.load") as json_load_mock,
        patch("weights_uploader.logger") as logger_mock,
        patch("builtins.open", new_callable=MagicMock) as open_mock,
        patch("weights_uploader.download_pretrained_model") as download_pretrained_model_mock,
    ):
        listdir_mock.return_value = ["weight1", "weight2"]
        join_mock.side_effect = lambda x, y: f"{x}/{y}"
        makedirs_mock.return_value = None
        client_instance_mock = MagicMock()
        client_instance_mock.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "head_object")

        boto3_client_mock.return_value = client_instance_mock
        open_mock.return_value.__enter__.return_value = MagicMock()
        json_load_mock.return_value = json.loads(mock_file_content)
        download_pretrained_model_mock.return_value = None  # Mock the download function

        client_instance_mock.upload_file.side_effect = ClientError({"Error": {}}, "upload_file")

        with pytest.raises(ClientError):
            main()
        logger_mock.error.assert_called()
