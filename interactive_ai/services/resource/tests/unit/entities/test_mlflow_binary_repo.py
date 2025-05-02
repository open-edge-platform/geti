# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from unittest.mock import patch

import pytest
from _pytest.fixtures import FixtureRequest
from minio import Minio, S3Error

from repos.mlflow_binary_repo import MLFlowBinaryRepo

from geti_types import ProjectIdentifier
from iai_core_py.adapters.binary_interpreters import RAWBinaryInterpreter


class TestMLFlowBinaryRepo:
    @staticmethod
    def __set_env_variables(request: FixtureRequest):
        """
        Set environment variables required for on-prem storage repo to be instantiated
        """
        os.environ["S3_CREDENTIALS_PROVIDER"] = "local"
        os.environ["S3_SECRET_KEY"] = "secret_key"
        os.environ["S3_ACCESS_KEY"] = "access_key"
        os.environ["S3_PRESIGNED_URL_ACCESS_KEY"] = "dummy_access_key"
        os.environ["S3_PRESIGNED_URL_SECRET_KEY"] = "dummy_secret_key"
        os.environ["S3_HOST"] = "s3_host"
        os.environ["FEATURE_FLAG_OBJECT_STORAGE_OP"] = "True"
        os.environ["BUCKET_NAME_MLFLOWEXPERIMENTS"] = "mlflowexperiments"

        def remove_env_variable(variable_name: str):
            if variable_name in os.environ:
                del os.environ[variable_name]

        request.addfinalizer(lambda: remove_env_variable("S3_CREDENTIALS_PROVIDER"))
        request.addfinalizer(lambda: remove_env_variable("S3_SECRET_KEY"))
        request.addfinalizer(lambda: remove_env_variable("S3_ACCESS_KEY"))
        request.addfinalizer(lambda: remove_env_variable("S3_PRESIGNED_URL_ACCESS_KEY"))
        request.addfinalizer(lambda: remove_env_variable("S3_PRESIGNED_URL_SECRET_KEY"))
        request.addfinalizer(lambda: remove_env_variable("S3_HOST"))
        request.addfinalizer(lambda: remove_env_variable("FEATURE_FLAG_OBJECT_STORAGE_OP"))
        request.addfinalizer(lambda: remove_env_variable("BUCKET_NAME_MLFLOWEXPERIMENTS"))

    def test_mlflow_binary_repo_delete_all(self, request, fxt_project) -> None:
        """
        Tests delete_all_under_project_dir method in the MLFlowBinaryRepo
        """
        self.__set_env_variables(request)
        mlflow_binary_repo = MLFlowBinaryRepo(
            identifier=ProjectIdentifier(
                workspace_id=fxt_project.workspace_id,
                project_id=fxt_project.id_,
            )
        )

        with patch.object(Minio, "remove_objects", return_value=[]) as mock_delete:
            mlflow_binary_repo.delete_all_under_project_dir()

        mock_delete.assert_called_once()

        side_effect = S3Error(code="", message="", resource="", request_id="", host_id="", response="")  # type: ignore[arg-type]
        with patch.object(Minio, "get_object", side_effect=side_effect) as mock_get, pytest.raises(FileNotFoundError):
            _ = mlflow_binary_repo.get_by_filename(
                filename="test_filename",
                binary_interpreter=RAWBinaryInterpreter(),
            )

        mock_get.assert_called_once_with(
            bucket_name="mlflowexperiments",
            object_name=f"organizations/00000000-0000-0000-0000-000000000001/workspaces/{fxt_project.workspace_id}/projects/{fxt_project.id_}/test_filename",
        )
