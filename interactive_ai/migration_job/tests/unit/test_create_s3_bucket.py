# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Tests the create_s3_bucket module."""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError

from migration_job import create_s3_bucket
from migration_job.create_s3_bucket import S3Client


def test_main():
    """Tests the main function."""
    s3_address = "S3AddressMock"
    s3_access_key = "S3AccessKeyMock"
    s3_secret_key = "S3SecretKeyMock"
    s3_bucket = "S3BucketMock"

    # Mock environment variables.
    os.environ.update(
        {
            "S3_ACCESS_KEY": s3_access_key,
            "S3_SECRET_KEY": s3_secret_key,
            "S3_BUCKET": s3_bucket,
            "S3_ADDRESS": s3_address,
        }
    )
    mock_s3_client = Mock(spec=S3Client)
    with patch("migration_job.create_s3_bucket.S3Client", return_value=mock_s3_client):
        create_s3_bucket.main()

    mock_s3_client.create_bucket.assert_called_once_with(bucket_name=s3_bucket)


@pytest.mark.parametrize(
    "s3_address,s3_access_key,s3_secret_key,s3_bucket",
    (
        (
            None,
            "S3AccessKeyMock",
            "S3SecretKeyMock",
            "S3BucketMock",
        ),
        (
            "S3AddressMock",
            None,
            "S3SecretKeyMock",
            "S3BucketMock",
        ),
        (
            "S3AddressMock",
            "S3AccessKeyMock",
            None,
            "S3BucketMock",
        ),
        (
            "S3AddressMock",
            "S3AccessKeyMock",
            "S3SecretKeyMock",
            None,
        ),
    ),
)
def test_main_unset_env_var(
    s3_access_key: str,
    s3_secret_key: str,
    s3_bucket: str,
    s3_address: str,
):
    """Tests the main function, negative case.

    Covers a scenario in which some required environment variables are not set.
    """
    # Mock environment variables.
    envs = {
        "S3_ACCESS_KEY": s3_access_key,
        "S3_SECRET_KEY": s3_secret_key,
        "S3_BUCKET": s3_bucket,
        "S3_ADDRESS": s3_address,
    }
    os.environ.update({key: val for key, val in envs.items() if val})
    for name, value in envs.items():
        if value is None and name in os.environ:
            os.environ.pop(name)

    with pytest.raises(EnvironmentError):
        create_s3_bucket.main()


@pytest.mark.parametrize(
    "side_effect, expected_result",
    [
        pytest.param(Mock(return_value="response-mock"), True),
        pytest.param(
            Mock(
                side_effect=ClientError(
                    error_response={"Error": {"Code": "404"}},
                    operation_name="HeadBucket",
                )
            ),
            False,
        ),
    ],
)
def test_bucket_exist(mocker, side_effect, expected_result):
    """Tests the bucket_exist function, positive case."""
    bucket_name_mock = "bucket-mock"
    endpoint_mock = "endpoint-mock"
    access_key_mock = "access-key-mock"
    secret_key_mock = "secret-key-mock"

    client_mock = Mock(head_bucket=side_effect)
    client_type_mock = mocker.patch("migration_job.create_s3_bucket.boto3.client", side_effect=(client_mock,))

    s3_client = S3Client(
        endpoint=endpoint_mock,
        access_key=access_key_mock,
        secret_key=secret_key_mock,
    )
    result = s3_client.bucket_exist(bucket_name=bucket_name_mock)

    result == expected_result
    client_type_mock.assert_called_once_with(
        "s3",
        aws_access_key_id=access_key_mock,
        endpoint_url=endpoint_mock,
        aws_secret_access_key=secret_key_mock,
        use_ssl=False,
    )


def test_bucket_exist_unexpected_err(mocker):
    """Tests the bucket_exist function.

    Covers the scenario in which the `bucket_exist` method raises an unexpected error.
    """
    endpoint = "http://localhost:9000"
    access_key = "access_key"
    secret_key = "secret_key"
    bucket_name = "my-bucket"

    s3_client = S3Client(endpoint, access_key, secret_key)
    mocked_head_bucket = Mock(
        side_effect=ClientError({"Error": {"Code": "403", "Message": "Not found"}}, "head_bucket")
    )
    s3_client.bucket_exist = mocked_head_bucket

    with pytest.raises(ClientError) as exc_info:
        s3_client.bucket_exist(bucket_name=bucket_name)
    assert exc_info.value.response["Error"]["Code"] == "403"


@patch.object(S3Client, "bucket_exist")
@patch("migration_job.create_s3_bucket.boto3.client")
def test_create_bucket_unexpected_err(mock_client, mock_bucket_exist):
    """Tests the create_bucket function.

    Covers the scenario in which the `create_bucket` method raises an unexpected error.
    """
    bucket_name_mock = "invalid-bucket-name"
    endpoint_mock = "endpoint-mock"
    access_key_mock = "access-key-mock"
    secret_key_mock = "secret-key-mock"

    err_mock = ClientError({"Error": {"Code": "404", "Message": "Bucket not found"}}, "create_bucket")
    s3_client = S3Client(endpoint=endpoint_mock, access_key=access_key_mock, secret_key=secret_key_mock)
    mock_s3_client = Mock()
    s3_client.client = mock_s3_client
    mock_s3_client.create_bucket.side_effect = err_mock
    mock_bucket_exist.return_value = False

    with pytest.raises(ClientError) as err_info:
        s3_client.create_bucket(bucket_name=bucket_name_mock)

    assert err_info.value.response == err_mock.response


@patch.object(S3Client, "bucket_exist")
@patch("migration_job.create_s3_bucket.boto3.client")
def test_create_bucket_new(mock_client, mock_bucket_exist):
    """Tests the create_bucket function.

    Covers the scenario in which the target bucket does not exist yet.
    """
    bucket_name_mock = "bucket-mock"
    endpoint_mock = "endpoint-mock"
    access_key_mock = "access-key-mock"
    secret_key_mock = "secret-key-mock"

    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    mock_bucket_exist.return_value = False

    s3_client = S3Client(endpoint=endpoint_mock, access_key=access_key_mock, secret_key=secret_key_mock)
    s3_client.create_bucket(bucket_name_mock)
    mock_client_instance.create_bucket.assert_called_once_with(Bucket=bucket_name_mock)
