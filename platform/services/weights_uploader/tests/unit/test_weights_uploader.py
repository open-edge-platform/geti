# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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


def test_main_success():
    with (
        patch("boto3.client") as boto3_client_mock,
        patch("os.listdir") as listdir_mock,
        patch("os.path.join") as join_mock,
        patch("weights_uploader.logger") as logger_mock,
    ):
        listdir_mock.return_value = ["weight1", "weight2"]
        join_mock.side_effect = lambda x, y: f"{x}/{y}"
        client_instance_mock = MagicMock()
        boto3_client_mock.return_value = client_instance_mock
        main()

        assert boto3_client_mock.called
        assert client_instance_mock.upload_file.call_count == 2
        logger_mock.info.assert_called()
        logger_mock.error.assert_not_called()


def test_main_upload_error():
    with (
        patch("boto3.client") as boto3_client_mock,
        patch("os.listdir") as listdir_mock,
        patch("os.path.join") as join_mock,
        patch("weights_uploader.logger") as logger_mock,
    ):
        listdir_mock.return_value = ["weight1"]
        join_mock.side_effect = lambda x, y: f"{x}/{y}"
        client_instance_mock = MagicMock()
        boto3_client_mock.return_value = client_instance_mock
        client_instance_mock.upload_file.side_effect = ClientError({"Error": {}}, "upload_file")

        with pytest.raises(ClientError):
            main()
        logger_mock.error.assert_called()
