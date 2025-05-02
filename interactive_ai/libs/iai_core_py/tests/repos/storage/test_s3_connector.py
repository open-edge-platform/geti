# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from unittest import mock
from unittest.mock import ANY, call, patch

import pytest
from minio import Minio
from minio.credentials import IamAwsProvider

from iai_core.repos.storage.s3_connector import S3_ADDRESS, S3Connector


@pytest.fixture
def fxt_s3_env_vars_on_prem():
    with mock.patch.dict(
        os.environ,
        {
            "S3_CREDENTIALS_PROVIDER": "local",
            "S3_HOST": "dummy_host",
            "S3_ACCESS_KEY": "dummy_access_key_1",
            "S3_SECRET_KEY": "dummy_secret_key_1",
            "S3_PRESIGNED_URL_ACCESS_KEY": "dummy_access_key_2",
            "S3_PRESIGNED_URL_SECRET_KEY": "dummy_secret_key_2",
        },
    ):
        yield


@pytest.fixture
def fxt_s3_env_vars_saas():
    with mock.patch.dict(
        os.environ,
        {
            "S3_CREDENTIALS_PROVIDER": "aws",
            "S3_HOST": "dummy_host",
            "AWS_ROLE_ARN": "dummy_role",
            "AWS_REGION": "dummy_region",
            "AWS_WEB_IDENTITY_TOKEN_FILE": "dummy_token_file",
        },
    ):
        yield


@pytest.fixture
def fxt_clear_s3_connector_cache():
    S3Connector.clear_client_cache()
    yield
    S3Connector.clear_client_cache()


def do_nothing(self, *args, **kwargs) -> None:
    return None


class TestS3Connector:
    def test_get_clients_on_prem(self, fxt_s3_env_vars_on_prem, fxt_clear_s3_connector_cache) -> None:
        with (
            patch.object(Minio, "__init__", return_value=None) as mock_minio_init,
            patch.object(IamAwsProvider, "__init__", return_value=None) as mock_iam_aws_provider,
        ):
            s3_regular_client, s3_presigned_client = S3Connector.get_clients()

            mock_minio_init.assert_has_calls(
                [
                    call(
                        endpoint="dummy_host",
                        secure=False,
                        access_key="dummy_access_key_1",
                        secret_key="dummy_secret_key_1",
                    ),
                    call(
                        endpoint="dummy_host",
                        secure=False,
                        access_key="dummy_access_key_2",
                        secret_key="dummy_secret_key_2",
                    ),
                ],
                any_order=True,
            )
            mock_iam_aws_provider.assert_not_called()
            assert s3_regular_client != s3_presigned_client
            # Verify that the clients are cached
            s3_regular_client_2, s3_presigned_client_2 = S3Connector.get_clients()
            assert s3_regular_client_2 == s3_regular_client
            assert s3_presigned_client_2 == s3_presigned_client

    def test_get_clients_saas(self, fxt_s3_env_vars_saas, fxt_clear_s3_connector_cache) -> None:
        with (
            patch.object(Minio, "__init__", return_value=None) as mock_minio_init,
            patch.object(IamAwsProvider, "__init__", return_value=None) as mock_iam_aws_provider,
        ):
            s3_regular_client, s3_presigned_client = S3Connector.get_clients()

            mock_minio_init.assert_has_calls(
                [
                    call(
                        endpoint=S3_ADDRESS,
                        secure=True,
                        region="dummy_region",
                        credentials=ANY,
                    ),
                ],
                any_order=True,
            )
            mock_iam_aws_provider.assert_called()
            assert s3_regular_client == s3_presigned_client
            # Verify that the clients are cached
            s3_regular_client_2, s3_presigned_client_2 = S3Connector.get_clients()
            assert s3_regular_client_2 == s3_regular_client
            assert s3_presigned_client_2 == s3_presigned_client

    def test_get_clients_multiprocessing(self, fxt_s3_env_vars_on_prem, fxt_clear_s3_connector_cache) -> None:
        PID_1 = 100
        PID_2 = 101
        with (
            patch.object(Minio, "__init__", return_value=None),
            patch.object(Minio, "__del__", return_value=None),
            patch.object(IamAwsProvider, "__init__", return_value=None),
            patch("os.getpid", return_value=PID_1),
        ):
            client_1_1, _ = S3Connector.get_clients()
            client_1_2, _ = S3Connector.get_clients()
        with (
            patch.object(Minio, "__init__", return_value=None),
            patch.object(Minio, "__del__", return_value=None),
            patch.object(IamAwsProvider, "__init__", return_value=None),
            patch("os.getpid", return_value=PID_2),
        ):
            client_2, _ = S3Connector.get_clients()

        assert client_1_1 == client_1_2
        assert client_1_1 != client_2
