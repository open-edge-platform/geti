# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from unittest.mock import ANY, MagicMock, patch

import pytest
from _pytest.fixtures import FixtureRequest
from geti_types import ID
from iai_core.repos.storage.storage_client import BinaryObjectType
from minio import Minio
from minio.datatypes import Object

from job.repos import BinaryStorageRepo

"""
This module tests the BinaryStorageRepo class.
"""


@pytest.mark.ProjectIEMsComponent
class TestBinaryStorageRepo:
    @staticmethod
    def __set_env_variables(request: FixtureRequest):
        """
        Set environment variables required for on-prem storage repo to be instantiated
        """
        os.environ["S3_CREDENTIALS_PROVIDER"] = "local"
        os.environ["S3_SECRET_KEY"] = "secret_key"
        os.environ["S3_ACCESS_KEY"] = "access_key"
        os.environ["S3_HOST"] = "s3_host"

        def remove_env_variable(variable_name: str):
            if variable_name in os.environ:
                del os.environ[variable_name]

        request.addfinalizer(lambda: remove_env_variable("S3_CREDENTIALS_PROVIDER"))
        request.addfinalizer(lambda: remove_env_variable("S3_SECRET_KEY"))
        request.addfinalizer(lambda: remove_env_variable("S3_ACCESS_KEY"))
        request.addfinalizer(lambda: remove_env_variable("S3_HOST"))

    @staticmethod
    def __create_temporary_file(request: FixtureRequest, filename: str):
        """
        Create a temporary empty file with cleanup
        """
        with open(filename, "w") as file:
            file.write("")

        def remove_file(filename: str):
            if os.path.exists(filename):
                os.remove(filename)

        request.addfinalizer(lambda: remove_file(filename))

    def test_init(self, request, fxt_mongo_id) -> None:
        # Arrange
        organization_id = ID(fxt_mongo_id(0))
        workspace_id = ID(fxt_mongo_id(1))
        project_id = ID(fxt_mongo_id(2))
        self.__set_env_variables(request=request)
        with (
            patch.object(Minio, "__init__", return_value=None) as mock_init_minio_client,
            patch("boto3.client", return_value=None) as mock_init_boto_client,
        ):
            # Act
            storage_repo = BinaryStorageRepo(
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
            )

            # Assert
            mock_init_minio_client.assert_called_once_with(
                endpoint=os.environ["S3_HOST"],
                secure=False,
                access_key=os.environ["S3_ACCESS_KEY"],
                secret_key=os.environ["S3_SECRET_KEY"],
            )
            mock_init_boto_client.assert_called_once_with(
                service_name="s3",
                aws_access_key_id=os.environ.get("S3_ACCESS_KEY", ""),
                aws_secret_access_key=os.environ.get("S3_SECRET_KEY", ""),
                endpoint_url=f"http://{os.environ['S3_HOST']}",
            )
            assert storage_repo.s3_project_root == os.path.join(
                "organizations",
                str(organization_id),
                "workspaces",
                str(workspace_id),
                "projects",
                str(project_id),
            )

    def test_get_object_types(self) -> None:
        expected_object_types = {
            BinaryObjectType.IMAGES,
            BinaryObjectType.VIDEOS,
            BinaryObjectType.THUMBNAILS,
            BinaryObjectType.MODELS,
            BinaryObjectType.TENSORS,
            BinaryObjectType.VPS_REFERENCE_FEATURES,
        }
        object_types = BinaryStorageRepo.get_object_types()

        assert set(object_types) == expected_object_types

    def test_get_all_objects_by_type(
        self,
        request: FixtureRequest,
        fxt_mongo_id,
    ):
        """
        Test the get_all_objects_by_type method.

        1. Arrange all variables such as IDs, paths and filenames in the manner that they would be on export
        2. Set environment variables for the repo to be instantiated
        3. Mock all s3-related methods.
         - The initialization of the minio client will be mocked
         - The bucket_exists method of minio will be mocked to always be true
         - The list_objects method returns a single mock object.
         - The fget_object method is mocked in such a way that it creates a single file with the name of the object
            that was requested.
        4. Call the method
        5. Assert that all the mocks were called
        """
        # Arrange
        organization_id = ID(fxt_mongo_id(0))
        workspace_id = ID(fxt_mongo_id(1))
        project_id = ID(fxt_mongo_id(2))
        dataset_storage_id = ID(fxt_mongo_id(3))

        object_type = BinaryObjectType.IMAGES
        object_basename = "dummy.name"
        object_name_from_project_root = os.path.join("dataset_storages", str(dataset_storage_id), object_basename)
        project_root = os.path.join(
            "organizations",
            str(organization_id),
            "workspaces",
            str(workspace_id),
            "projects",
            str(project_id),
        )
        object_name = os.path.join(project_root, object_name_from_project_root)

        temp_folder = "/tmp/dummy"
        local_path = os.path.join(temp_folder, object_name_from_project_root)

        self.__set_env_variables(request=request)

        mock_object = MagicMock()
        mock_object.object_name = object_name

        with (
            patch("boto3.client", return_value=None),
            patch("tempfile.mkdtemp"),
            patch.object(Minio, "list_objects", return_value=[mock_object]) as mock_list_objects,
            patch.object(Minio, "bucket_exists", return_value=True) as mock_bucket_exists,
            patch.object(Minio, "fget_object", return_value=None) as mock_fget_object,
        ):
            # Create the effect of creating a file when fget_object is called, as it would behave on S3 call.
            mock_fget_object.side_effect = (
                lambda bucket_name, file_path, object_name: TestBinaryStorageRepo.__create_temporary_file(
                    request=request, filename=os.path.basename(object_name)
                )
            )

            # Act
            storage_repo = BinaryStorageRepo(
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
            )
            for (
                local_path_iter,
                object_name_iter,
            ) in storage_repo.get_all_objects_by_type(object_type=BinaryObjectType.IMAGES, target_folder=temp_folder):
                assert local_path_iter == local_path
                assert object_name_iter == object_name_from_project_root

            # Assert
            mock_list_objects.assert_called_once_with(
                bucket_name=object_type.bucket_name(),
                prefix=project_root + "/",
                recursive=True,
            )
            mock_bucket_exists.assert_called_once_with(bucket_name=object_type.bucket_name())
            mock_fget_object.assert_called_once_with(
                bucket_name=object_type.bucket_name(),
                file_path=local_path,
                object_name=object_name,
            )

    def test_store_objects_by_type(
        self,
        request: FixtureRequest,
        fxt_mongo_id,
    ):
        """
        Test the store_objects_by_type method.

        1. Arrange all variables such as IDs, paths and filenames.
        2. Set environment variables for the repo to be instantiated .
        3. Mock the S3 initialization and fput_object method.
        4. Call the method
        5. Assert that the mock put request was called once for every bucket.
        """
        # Arrange
        organization_id = ID(fxt_mongo_id(0))
        workspace_id = ID(fxt_mongo_id(1))
        project_id = ID(fxt_mongo_id(2))
        dataset_storage_id = ID(fxt_mongo_id(3))

        object_type = BinaryObjectType.IMAGES
        object_basename = "dummy.name"
        project_root = os.path.join(
            "organizations",
            str(organization_id),
            "workspaces",
            str(workspace_id),
            "projects",
            str(project_id),
        )
        object_name_from_project_root = os.path.join("dataset_storages", str(dataset_storage_id), object_basename)
        object_name = os.path.join(project_root, object_name_from_project_root)
        temp_file_path = "/tmp/dummy"
        local_path = os.path.join(temp_file_path, object_basename)

        local_and_remote_paths = [(local_path, object_name_from_project_root)]

        self.__set_env_variables(request=request)
        self.__create_temporary_file(request=request, filename=object_basename)

        with (
            patch("boto3.client", return_value=None),
            patch.object(Minio, "__init__", return_value=None),
            patch.object(Minio, "fput_object", return_value=None) as mock_put_object,
        ):
            # Act
            storage_repo = BinaryStorageRepo(
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
            )
            storage_repo.store_objects_by_type(object_type=object_type, local_and_remote_paths=local_and_remote_paths)

            # Assert
            mock_put_object.assert_called_once_with(
                bucket_name=object_type.bucket_name(),
                object_name=object_name,
                file_path=local_path,
            )

    def test_delete_all_objects_by_type(self, request: FixtureRequest, fxt_ote_id) -> None:
        # Arrange
        self.__set_env_variables(request=request)
        organization_id = fxt_ote_id(0)
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        project_root = f"organizations/{str(organization_id)}/workspaces/{str(workspace_id)}/projects/{str(project_id)}"
        objects = [
            Object(
                bucket_name="images",
                object_name=f"{project_root}/dataset_storages/{str(dataset_storage_id)}/foo.jpg",
            ),
            Object(
                bucket_name="images",
                object_name=f"{project_root}/dataset_storages/{str(dataset_storage_id)}/bar.png",
            ),
        ]
        with (
            patch("boto3.client", return_value=None),
            patch.object(Minio, "__init__", return_value=None),
            patch.object(Minio, "list_objects", return_value=objects) as mock_list_objects,
            patch.object(Minio, "remove_objects", return_value=[]) as mock_remove_objects,
        ):
            # Act
            storage_repo = BinaryStorageRepo(
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
            )
            storage_repo.delete_all_objects_by_type(object_type=BinaryObjectType.IMAGES)

        # Assert
        mock_list_objects.assert_called_once_with(bucket_name="images", prefix=project_root + "/", recursive=True)
        mock_remove_objects.assert_called_once_with(bucket_name="images", delete_object_list=ANY)
        assert [obj._name for obj in mock_remove_objects.call_args.kwargs["delete_object_list"]] == [
            obj.object_name for obj in objects
        ]
