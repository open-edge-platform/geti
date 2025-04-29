# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import io
import os
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from minio import InvalidResponseError, Minio
from urllib3.exceptions import ReadTimeoutError

from sc_sdk.adapters.binary_interpreters import RAWBinaryInterpreter
from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.repos.storage.binary_repo import BinaryRepo
from sc_sdk.repos.storage.binary_repos import (
    CodeDeploymentBinaryRepo,
    ImageBinaryRepo,
    ModelBinaryRepo,
    TensorBinaryRepo,
    ThumbnailBinaryRepo,
    VideoBinaryRepo,
)
from sc_sdk.repos.storage.object_storage import (
    ObjectStorageClient,
    reinit_client_and_retry_on_timeout,
    retry_on_rate_limit,
)
from sc_sdk.repos.storage.s3_connector import S3Connector
from sc_sdk.repos.storage.storage_client import BinaryObjectType

from geti_types import DatasetStorageIdentifier
from geti_types.session import DEFAULT_ORGANIZATION_ID


def set_object_storage_env_variables(s3_credentials_provider: str):
    os.environ["FEATURE_FLAG_OBJECT_STORAGE_OP"] = "true"
    os.environ["BUCKET_NAME_IMAGES"] = "images"
    os.environ["BUCKET_NAME_VIDEOS"] = "videos"
    os.environ["BUCKET_NAME_TENSORS"] = "tensors"
    os.environ["BUCKET_NAME_MODELS"] = "models"
    os.environ["BUCKET_NAME_THUMBNAILS"] = "thumbnails"
    os.environ["BUCKET_NAME_CODEDEPLOYMENTS"] = "codedeployments"
    os.environ["S3_CREDENTIALS_PROVIDER"] = s3_credentials_provider
    os.environ["S3_HOST"] = "dummy_host"
    if s3_credentials_provider == "local":
        os.environ["S3_ACCESS_KEY"] = "dummy"
        os.environ["S3_SECRET_KEY"] = "dummy"
        os.environ["S3_PRESIGNED_URL_ACCESS_KEY"] = "dummy_access_key"
        os.environ["S3_PRESIGNED_URL_SECRET_KEY"] = "dummy_secret_key"
    elif s3_credentials_provider == "aws":
        os.environ["AWS_ROLE_ARN"] = "dummy_role"
        os.environ["AWS_REGION"] = "dummy_region"
        os.environ["AWS_WEB_IDENTITY_TOKEN_FILE"] = "dummy_file"
    else:
        raise ValueError("Only 'aws' and 'local' are valid credentials providers")


def unset_object_storage_env_variables():
    os.environ.pop("FEATURE_FLAG_OBJECT_STORAGE_OP", None)
    os.environ.pop("S3_ACCESS_KEY", None)
    os.environ.pop("S3_SECRET_KEY", None)
    os.environ.pop("S3_PRESIGNED_URL_ACCESS_KEY", None)
    os.environ.pop("S3_PRESIGNED_URL_SECRET_KEY", None)
    os.environ.pop("BUCKET_NAME_IMAGES", None)
    os.environ.pop("BUCKET_NAME_VIDEOS", None)
    os.environ.pop("BUCKET_NAME_TENSORS", None)
    os.environ.pop("BUCKET_NAME_MODELS", None)
    os.environ.pop("BUCKET_NAME_THUMBNAILS", None)
    os.environ.pop("BUCKET_NAME_CODEDEPLOYMENTS", None)
    os.environ.pop("S3_CREDENTIALS_PROVIDER", None)


@pytest.mark.ScSdkComponent
class TestBinaryRepoS3Storage:
    @pytest.fixture(
        params=[
            t
            for t in BinaryObjectType
            if t
            not in [
                BinaryObjectType.UNDEFINED,
                BinaryObjectType.MLFLOW_EXPERIMENTS,
                BinaryObjectType.VPS_REFERENCE_FEATURES,
                BinaryObjectType.RESULT_MEDIA,
            ]
        ]
    )
    def fxt_binary_object_type(self, request):
        return request.param

    @pytest.fixture()
    def fxt_binary_repo(
        self,
        fxt_binary_object_type: BinaryObjectType,
        fxt_dataset_storage_identifier,
        fxt_project_identifier,
        fxt_model_storage_identifier,
    ):
        map = {
            BinaryObjectType.MODELS: (ModelBinaryRepo, fxt_model_storage_identifier),
            BinaryObjectType.IMAGES: (ImageBinaryRepo, fxt_dataset_storage_identifier),
            BinaryObjectType.VIDEOS: (VideoBinaryRepo, fxt_dataset_storage_identifier),
            BinaryObjectType.THUMBNAILS: (ThumbnailBinaryRepo, fxt_dataset_storage_identifier),
            BinaryObjectType.TENSORS: (TensorBinaryRepo, fxt_dataset_storage_identifier),
            BinaryObjectType.CODE_DEPLOYMENTS: (CodeDeploymentBinaryRepo, fxt_project_identifier),
        }
        repo, identifier = map[fxt_binary_object_type]
        yield lambda: repo(identifier)
        S3Connector.clear_client_cache()

    def test_get_by_filename_s3(
        self,
        request,
        tmp_path,
        fxt_binary_object_type,
        fxt_binary_repo,
        fxt_http_response,
    ) -> None:
        # Enable feature flag
        set_object_storage_env_variables(s3_credentials_provider="local")
        request.addfinalizer(unset_object_storage_env_variables)

        # Mock Minio methods
        with patch.object(Minio, "get_object", return_value=fxt_http_response(data=b"dummy_bytes")) as mock_get_object:
            # Call the tested method
            binary_repo = fxt_binary_repo()
            result = binary_repo.get_by_filename(filename="dummy_file", binary_interpreter=RAWBinaryInterpreter())

            # Assert the right methods were called and the result is as expected
            assert result == RAWBinaryInterpreter().interpret(io.BytesIO(b"dummy_bytes"), filename="dummy_file")
            expected_object_name_base = os.path.join(
                "organizations",
                str(DEFAULT_ORGANIZATION_ID),
                "workspaces",
                str(binary_repo.identifier.workspace_id),
                "projects",
                str(binary_repo.identifier.project_id),
            )
            if isinstance(binary_repo.identifier, ModelStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "model_storages", binary_repo.identifier.model_storage_id
                )
            elif isinstance(binary_repo.identifier, DatasetStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "dataset_storages", binary_repo.identifier.dataset_storage_id
                )
            expected_object_name = os.path.join(expected_object_name_base, "dummy_file")
            mock_get_object.assert_called_once_with(
                bucket_name=fxt_binary_object_type.bucket_name(),
                object_name=expected_object_name,
            )

    def test_get_path_or_presigned_url_s3(
        self,
        request,
        tmp_path,
        fxt_binary_object_type,
        fxt_binary_repo,
    ) -> None:
        # Enable feature flag
        set_object_storage_env_variables(s3_credentials_provider="local")
        request.addfinalizer(unset_object_storage_env_variables)

        # Mock minio methods
        with patch.object(Minio, "presigned_get_object", return_value="dummy_presigned_url") as mock_get_presigned_url:
            # Call the tested method
            binary_repo = fxt_binary_repo()
            result = binary_repo.get_path_or_presigned_url(filename="dummy_file")

            # Assert the right methods were called and the result is as expected
            assert result == "dummy_presigned_url"
            expected_object_name_base = os.path.join(
                "organizations",
                str(DEFAULT_ORGANIZATION_ID),
                "workspaces",
                str(binary_repo.identifier.workspace_id),
                "projects",
                str(binary_repo.identifier.project_id),
            )
            if isinstance(binary_repo.identifier, ModelStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "model_storages", binary_repo.identifier.model_storage_id
                )
            elif isinstance(binary_repo.identifier, DatasetStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "dataset_storages", binary_repo.identifier.dataset_storage_id
                )
            expected_object_name = os.path.join(expected_object_name_base, "dummy_file")
            mock_get_presigned_url.assert_called_once_with(
                bucket_name=fxt_binary_object_type.bucket_name(),
                object_name=expected_object_name,
                expires=timedelta(minutes=15),
                response_headers=None,
            )

    @pytest.mark.parametrize(
        "data_source_type, overwrite, remove_source",
        [
            ("bytes", True, False),
            ("bytes", False, False),
            ("file", True, True),
            ("file", True, False),
            ("file", False, True),
            ("file", False, False),
        ],
        ids=[
            "saving bytes with overwrite",
            "saving bytes without overwrite",
            "saving file with overwrite and remove source",
            "saving file with overwrite and without removing source",
            "saving file without overwriting and with remove source",
            "saving file without overwrite and without removing source",
        ],
    )
    def test_save_s3(
        self,
        request,
        tmp_path,
        fxt_binary_object_type,
        fxt_binary_repo,
        fxt_mongo_id,
        data_source_type,
        overwrite,
        remove_source,
    ) -> None:
        # Enable feature flag
        set_object_storage_env_variables(s3_credentials_provider="local")
        request.addfinalizer(unset_object_storage_env_variables)

        # Create source file or bytes
        dummy_bytes = b"dummy_content"
        if data_source_type == "file":
            src_file_basename = "myfile.jpg"
            src_file_path = tmp_path / src_file_basename
            src_file_path.touch()
            src_file_path.write_bytes(dummy_bytes)
            source_file_or_bytes: str | bytes = str(src_file_path)
        else:
            source_file_or_bytes = dummy_bytes

        # Mock Minio related methods
        with (
            patch.object(ObjectStorageClient, "exists", return_value=False),
            patch.object(Minio, "fput_object", return_value=None) as mock_fput_object,
            patch.object(Minio, "put_object", return_value=None) as mock_put_object,
        ):
            # Call the tested method
            filename = str(fxt_mongo_id(1)) + ".jpg"
            binary_repo = fxt_binary_repo()
            binary_repo.save(
                dst_file_name=filename,
                data_source=source_file_or_bytes,
                overwrite=overwrite,
                remove_source=remove_source,
            )

            # Assert that the correct methods were called for the appropriate input type
            expected_object_name_base = os.path.join(
                "organizations",
                str(DEFAULT_ORGANIZATION_ID),
                "workspaces",
                str(binary_repo.identifier.workspace_id),
                "projects",
                str(binary_repo.identifier.project_id),
            )
            if isinstance(binary_repo.identifier, ModelStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "model_storages", binary_repo.identifier.model_storage_id
                )
            elif isinstance(binary_repo.identifier, DatasetStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "dataset_storages", binary_repo.identifier.dataset_storage_id
                )
            expected_object_name = os.path.join(expected_object_name_base, str(fxt_mongo_id(1)) + ".jpg")
            if data_source_type == "file":
                mock_fput_object.assert_called_once_with(
                    bucket_name=fxt_binary_object_type.bucket_name(),
                    object_name=expected_object_name,
                    file_path=source_file_or_bytes,
                )
                mock_put_object.assert_not_called()
            else:
                mock_put_object.assert_called_once()
                mock_fput_object.assert_not_called()

        # If remove source is true, assert that the source file no longer exists
        if remove_source and isinstance(source_file_or_bytes, str):
            assert not os.path.exists(source_file_or_bytes)
            src_file_basename = "myfile.jpg"
            src_file_path = tmp_path / src_file_basename
            src_file_path.touch()
            src_file_path.write_bytes(dummy_bytes)
            source_file_or_bytes = str(src_file_path)

        # If overwrite is disabled, check that overwriting at the same url raises the correct error
        if not overwrite:
            with pytest.raises(FileExistsError), patch.object(ObjectStorageClient, "exists", return_value=True):
                binary_repo.save(
                    dst_file_name=filename,
                    data_source=source_file_or_bytes,
                    overwrite=overwrite,
                    remove_source=remove_source,
                )

    def test_export_group_s3(
        self,
        request,
        fxt_binary_object_type,
        fxt_binary_repo,
        fxt_dataset_storage,
        fxt_s3_object,
    ) -> None:
        # Enable feature flag
        set_object_storage_env_variables(s3_credentials_provider="local")
        request.addfinalizer(unset_object_storage_env_variables)

        dummy_s3_object = fxt_s3_object(bucket_name="images", object_name="image1.jpg")
        temp_folder_path = os.path.join(os.getcwd(), "tmp_test_path")

        def _remove_temp_folder(folder_path):
            if os.path.exists(folder_path):
                os.rmdir(folder_path)

        request.addfinalizer(lambda: _remove_temp_folder(folder_path=temp_folder_path))

        # Patch minio related methods
        with (
            patch.object(Minio, "bucket_exists", return_value=True) as mock_bucket_exists,
            patch.object(Minio, "list_objects", return_value=[dummy_s3_object]) as mock_list_objects,
            patch.object(Minio, "fget_object", return_value=None) as mock_fget_object,
        ):
            binary_repo = fxt_binary_repo()
            binary_repo.export_group(target_directory=temp_folder_path)

            mock_bucket_exists.assert_called_once_with(fxt_binary_object_type.bucket_name())
            expected_prefix = os.path.join(
                "organizations",
                str(DEFAULT_ORGANIZATION_ID),
                "workspaces",
                str(binary_repo.identifier.workspace_id),
                "projects",
                str(binary_repo.identifier.project_id),
            )
            if isinstance(binary_repo.identifier, ModelStorageIdentifier):
                expected_prefix = os.path.join(
                    expected_prefix, "model_storages", binary_repo.identifier.model_storage_id
                )
            elif isinstance(binary_repo.identifier, DatasetStorageIdentifier):
                expected_prefix = os.path.join(
                    expected_prefix, "dataset_storages", binary_repo.identifier.dataset_storage_id
                )
            mock_list_objects.assert_called_once_with(
                bucket_name=fxt_binary_object_type.bucket_name(),
                prefix=expected_prefix + "/",
            )
            mock_fget_object.assert_called_once_with(
                bucket_name=fxt_binary_object_type.bucket_name(),
                object_name=dummy_s3_object.object_name,
                file_path=os.path.join(temp_folder_path, dummy_s3_object.object_name),
            )

    def test_delete_by_filename_s3(self, request, fxt_binary_object_type, fxt_binary_repo) -> None:
        # Enable feature flag
        set_object_storage_env_variables(s3_credentials_provider="local")
        request.addfinalizer(unset_object_storage_env_variables)

        # Patch minio related methods
        with patch.object(Minio, "remove_object", return_value=None) as mock_remove_object:
            # Call the tested method
            binary_repo = fxt_binary_repo()
            binary_repo.delete_by_filename(filename="dummy_file")

            # Assert the minio deletion was correctly called
            expected_object_name_base = os.path.join(
                "organizations",
                str(DEFAULT_ORGANIZATION_ID),
                "workspaces",
                str(binary_repo.identifier.workspace_id),
                "projects",
                str(binary_repo.identifier.project_id),
            )
            if isinstance(binary_repo.identifier, ModelStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "model_storages", binary_repo.identifier.model_storage_id
                )
            elif isinstance(binary_repo.identifier, DatasetStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "dataset_storages", binary_repo.identifier.dataset_storage_id
                )
            expected_object_name = os.path.join(expected_object_name_base, "dummy_file")
            mock_remove_object.assert_called_once_with(
                object_name=expected_object_name,
                bucket_name=fxt_binary_object_type.bucket_name(),
            )

    def test_delete_all_s3(
        self,
        request,
        fxt_binary_object_type,
        fxt_binary_repo,
        fxt_dataset_storage,
    ) -> None:
        # Enable feature flag
        set_object_storage_env_variables(s3_credentials_provider="local")
        request.addfinalizer(unset_object_storage_env_variables)

        # Patch minio related methods
        with (
            patch.object(Minio, "list_objects", return_value=["dummy_object_1", "dummy_object_2"]) as mock_list_objects,
            patch.object(Minio, "remove_objects", return_value=[]) as mock_remove_objects,
        ):
            # Call the tested method
            binary_repo = fxt_binary_repo()
            binary_repo.delete_all()

            # Assert that the mocked minio methods were called correctly
            expected_prefix = os.path.join(
                "organizations",
                str(DEFAULT_ORGANIZATION_ID),
                "workspaces",
                str(binary_repo.identifier.workspace_id),
                "projects",
                str(binary_repo.identifier.project_id),
            )
            if isinstance(binary_repo.identifier, ModelStorageIdentifier):
                expected_prefix = os.path.join(
                    expected_prefix, "model_storages", binary_repo.identifier.model_storage_id
                )
            elif isinstance(binary_repo.identifier, DatasetStorageIdentifier):
                expected_prefix = os.path.join(
                    expected_prefix, "dataset_storages", binary_repo.identifier.dataset_storage_id
                )
            mock_list_objects.assert_called_once_with(
                fxt_binary_object_type.bucket_name(),
                prefix=expected_prefix + "/",
                recursive=True,
            )
            mock_remove_objects.assert_called_once()

    def test_get_size_on_storage_for_url_s3(self, request, fxt_binary_object_type, fxt_binary_repo) -> None:
        # Enable feature flag
        set_object_storage_env_variables(s3_credentials_provider="local")
        request.addfinalizer(unset_object_storage_env_variables)

        # Create a dummy URL and a dummy object to be returned by stat_object
        dummy_filename = "dummy_file"

        class DummyStatObject:
            def __init__(self, size) -> None:
                self.size = size

        # Mock minio related methods
        with patch.object(Minio, "stat_object", return_value=DummyStatObject(size=10)) as mock_stat_object:
            # Call the tested method
            binary_repo = fxt_binary_repo()
            binary_repo.get_object_size(filename=dummy_filename)

            # Assert that the mocked minio methods were called correctly
            expected_object_name_base = os.path.join(
                "organizations",
                str(DEFAULT_ORGANIZATION_ID),
                "workspaces",
                str(binary_repo.identifier.workspace_id),
                "projects",
                str(binary_repo.identifier.project_id),
            )
            if isinstance(binary_repo.identifier, ModelStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "model_storages", binary_repo.identifier.model_storage_id
                )
            elif isinstance(binary_repo.identifier, DatasetStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "dataset_storages", binary_repo.identifier.dataset_storage_id
                )
            expected_object_name = os.path.join(expected_object_name_base, dummy_filename)
            mock_stat_object.assert_called_once_with(
                bucket_name=fxt_binary_object_type.bucket_name(), object_name=expected_object_name
            )

    def test_exists_s3(self, request, fxt_binary_object_type, fxt_binary_repo) -> None:
        # Enable feature flag
        set_object_storage_env_variables(s3_credentials_provider="local")
        request.addfinalizer(unset_object_storage_env_variables)

        # Mock minio method
        with patch.object(Minio, "stat_object", return_value=None) as mock_stat_object:
            # Call the tested methodz
            binary_repo = fxt_binary_repo()
            result = binary_repo.exists(filename="dummy_file")

            # Assert the object exists, as stat_object didn't raise an error, and assert the mocks were called
            assert result is True
            # Assert that the mocked minio methods were called correctly
            expected_object_name_base = os.path.join(
                "organizations",
                str(DEFAULT_ORGANIZATION_ID),
                "workspaces",
                str(binary_repo.identifier.workspace_id),
                "projects",
                str(binary_repo.identifier.project_id),
            )
            if isinstance(binary_repo.identifier, ModelStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "model_storages", binary_repo.identifier.model_storage_id
                )
            elif isinstance(binary_repo.identifier, DatasetStorageIdentifier):
                expected_object_name_base = os.path.join(
                    expected_object_name_base, "dataset_storages", binary_repo.identifier.dataset_storage_id
                )
            expected_object_name = os.path.join(expected_object_name_base, "dummy_file")
            mock_stat_object.assert_called_once_with(
                bucket_name=fxt_binary_object_type.bucket_name(),
                object_name=expected_object_name,
            )

    def test_retry_on_rate_limit(self, request) -> None:
        # Create a mock function and decorate it
        mock_function = Mock(side_effect=[InvalidResponseError(429, body="dummy", content_type="dummy"), "success"])
        decorated_function = retry_on_rate_limit()(mock_function)

        result = decorated_function()
        # Check that the function succeeded on the second call and the mock was called twice
        assert result == "success"
        assert mock_function.call_count == 2

        # Test that the function does not retry for non-429 errors
        mock_function.side_effect = InvalidResponseError(500, body="dummy", content_type="dummy")
        with pytest.raises(InvalidResponseError):
            decorated_function()

        # Ensure the function was only called once this time
        assert mock_function.call_count == 3

    def test_reinit_client_and_retry_on_timeout(self, request) -> None:
        set_object_storage_env_variables(s3_credentials_provider="local")
        request.addfinalizer(unset_object_storage_env_variables)

        # Create a mock function and decorate it
        class DummyClass:
            """dummyclass"""

        mock_function = Mock(
            side_effect=[ReadTimeoutError(pool=None, url="someurl", message="test error"), "success"]  # type: ignore[arg-type]
        )
        decorated_function = reinit_client_and_retry_on_timeout(mock_function)

        result = decorated_function(DummyClass())  # pass the dummy class as 'self'
        # Check that the function succeeded on the second call and the mock was called twice
        assert result == "success"
        assert mock_function.call_count == 2

        # Test that the function does not retry for non-429 errors
        mock_function.side_effect = RuntimeError("error triggered for test purposes")
        with pytest.raises(RuntimeError):
            decorated_function(DummyClass())

        # Ensure the function was only called once this time
        assert mock_function.call_count == 3


@pytest.mark.ScSdkComponent
class TestBinaryRepoLocalStorage:
    def test_get_by_filename_local(self, request, tmp_path, fxt_dataset_identifier, fxt_dataset_storage) -> None:
        # Save bytes
        binary_repo = ImageBinaryRepo(fxt_dataset_identifier)
        filename = binary_repo.save(dst_file_name="dummy.file", data_source=b"dummy_content")
        request.addfinalizer(binary_repo.delete_all)

        # Fetch bytes and assert they are the same
        result_bytes = binary_repo.get_by_filename(filename=filename, binary_interpreter=RAWBinaryInterpreter())
        assert result_bytes == b"dummy_content"

    def test_get_path_or_presigned_url_local(
        self, request, tmp_path, fxt_dataset_storage_identifier, fxt_dataset_storage
    ) -> None:
        # Save bytes
        binary_repo = ImageBinaryRepo(fxt_dataset_storage_identifier)
        filename = binary_repo.save(dst_file_name="dummy.file", data_source=b"dummy_content")
        request.addfinalizer(binary_repo.delete_all)

        # Get path for bytes and assert it exists
        result_path = binary_repo.get_path_or_presigned_url(filename=filename)

        assert isinstance(result_path, Path)
        assert os.path.exists(result_path)

    @pytest.mark.parametrize(
        "data_source_type, overwrite, remove_source",
        [
            ("bytes", True, False),
            ("bytes", False, False),
            ("file", True, True),
            ("file", True, False),
            ("file", False, True),
            ("file", False, False),
        ],
        ids=[
            "saving bytes with overwrite",
            "saving bytes without overwrite",
            "saving file with overwrite and remove source",
            "saving file with overwrite and without removing source",
            "saving file without overwriting and with remove source",
            "saving file without overwrite and without removing source",
        ],
    )
    def test_save_local(
        self,
        request,
        tmp_path,
        fxt_dataset_storage_identifier,
        fxt_mongo_id,
        data_source_type,
        overwrite,
        remove_source,
    ) -> None:
        # Create dummy source file or bytes
        dummy_bytes = b"dummy_content"
        if data_source_type == "file":
            src_file_basename = "myfile.jpg"
            src_file_path = tmp_path / src_file_basename
            src_file_path.touch()
            src_file_path.write_bytes(dummy_bytes)
            source_file_or_bytes: str | bytes = str(src_file_path)
        else:
            source_file_or_bytes = dummy_bytes

        # Save the source file or bytes
        filename = str(fxt_mongo_id(1)) + ".jpg"
        binary_repo = ImageBinaryRepo(fxt_dataset_storage_identifier)
        binary_repo.save(
            dst_file_name=filename,
            data_source=source_file_or_bytes,
            overwrite=overwrite,
            remove_source=remove_source,
        )
        request.addfinalizer(binary_repo.delete_all)

        # If remove_source is enabled, assert the source file doesn't exist anymore and create new source bytes
        # for the rest of the test
        if remove_source and isinstance(source_file_or_bytes, str):
            assert not os.path.exists(source_file_or_bytes)
            src_file_basename = "myfile.jpg"
            src_file_path = tmp_path / src_file_basename
            src_file_path.touch()
            src_file_path.write_bytes(dummy_bytes)
            source_file_or_bytes = str(src_file_path)

        if overwrite:
            # If overwrite is enabled, check that overwriting at the same url does not raise an error
            binary_repo.save(
                dst_file_name=filename,
                data_source=source_file_or_bytes,
                overwrite=overwrite,
                remove_source=remove_source,
            )
        else:
            # If overwrite is disabled, check that overwriting at the same url raises the correct error
            with pytest.raises(FileExistsError):
                binary_repo.save(
                    dst_file_name=filename,
                    data_source=source_file_or_bytes,
                    overwrite=overwrite,
                    remove_source=remove_source,
                )

        # Assert that the file or bytes were properly saved and are obtainable from the repo
        result_bytes = binary_repo.get_by_filename(filename=filename, binary_interpreter=RAWBinaryInterpreter())
        assert result_bytes == dummy_bytes

    def test_delete_by_filename_local(self, request, fxt_dataset_storage_identifier, fxt_dataset_storage) -> None:
        # Save dummy bytes
        binary_repo = ImageBinaryRepo(fxt_dataset_storage_identifier)
        filename = binary_repo.save(dst_file_name="dummy.file", data_source=b"dummy_content")
        request.addfinalizer(binary_repo.delete_all)

        # Delete dummy bytes and assert that they are no longer obtainable
        binary_repo.delete_by_filename(filename=filename)
        with pytest.raises(FileNotFoundError):
            binary_repo.get_by_filename(filename=filename, binary_interpreter=RAWBinaryInterpreter())

    def test_delete_all_local(self, request, fxt_ote_id) -> None:
        # Create two different workspaces and dataset storages, and two different binary repos
        ws_1_id, ws_2_id = fxt_ote_id(1), fxt_ote_id(2)
        proj_1_id, proj_2_id = fxt_ote_id(3), fxt_ote_id(4)
        ds_1 = DatasetStorageIdentifier(workspace_id=ws_1_id, project_id=proj_1_id, dataset_storage_id=fxt_ote_id(5))
        ds_2 = DatasetStorageIdentifier(workspace_id=ws_2_id, project_id=proj_2_id, dataset_storage_id=fxt_ote_id(6))
        binary_repo_1 = ImageBinaryRepo(ds_1)
        binary_repo_2 = ImageBinaryRepo(ds_2)
        request.addfinalizer(binary_repo_1.delete_all)
        request.addfinalizer(binary_repo_2.delete_all)
        saved_files_per_repo: dict[BinaryRepo, list[str]] = defaultdict(list)

        # Save bytes to both binary repos
        for repo_idx, (binary_repo, _dataset_storage_identifier) in enumerate(
            ((binary_repo_1, ds_1), (binary_repo_2, ds_2)), start=1
        ):
            for file_idx in range(2):
                dst_file_basename = f"test_file_{repo_idx}_{file_idx}"
                filename = binary_repo.save(
                    dst_file_name=dst_file_basename,
                    data_source=b"dummy_data",
                )
                saved_files_per_repo[binary_repo].append(filename)

        # Remove everything from one of the binary repos
        binary_repo_1.delete_all()

        # Assert the first binary repo is empty
        for filename in saved_files_per_repo[binary_repo_1]:
            with pytest.raises(FileNotFoundError):
                binary_repo_1.get_by_filename(filename=filename, binary_interpreter=RAWBinaryInterpreter())

        # Assert the second binary repo still contains all the data
        for filename in saved_files_per_repo[binary_repo_2]:
            binary_repo_2.get_by_filename(filename=filename, binary_interpreter=RAWBinaryInterpreter())

    def test_get_object_size_local(self, request, fxt_dataset_storage_identifier, fxt_dataset_storage) -> None:
        # Save dummy data
        binary_repo = ImageBinaryRepo(fxt_dataset_storage_identifier)
        filename = binary_repo.save(dst_file_name="dummy.file", data_source=b"dummy_content")
        request.addfinalizer(binary_repo.delete_all)

        # Call the tested method and assert the storage size is correct
        result_size = binary_repo.get_object_size(filename=filename)
        assert result_size == len(b"dummy_content")

    def test_exists_local(self, request, fxt_dataset_storage_identifier, fxt_dataset_storage) -> None:
        binary_repo = ImageBinaryRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(binary_repo.delete_all)

        # Save bytes and assert "exists" is true
        filename = binary_repo.save(dst_file_name="dummy.file", data_source=b"dummy_content")
        assert binary_repo.exists(filename=filename)

        # Remove the data at the URL and assert "exists" is now false
        binary_repo.delete_by_filename(filename)
        assert not binary_repo.exists(filename=filename)
