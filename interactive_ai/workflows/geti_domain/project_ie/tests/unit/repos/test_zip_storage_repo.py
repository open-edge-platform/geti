# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
import os
from unittest.mock import patch

import pytest
from _pytest.fixtures import FixtureRequest
from geti_types import ID
from minio import Minio

from job.repos.zip_storage_repo import ZipStorageRepo


@pytest.mark.ProjectIEMsComponent
class TestZipStorageRepo:
    @staticmethod
    def __set_env_variables(request: FixtureRequest):
        """
        Set environment variables required for on-prem upload storage repo to be instantiated
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

    def test_init(self, request, fxt_mongo_id) -> None:
        # Arrange
        organization_id = ID(fxt_mongo_id(0))
        workspace_id = ID(fxt_mongo_id(1))
        self.__set_env_variables(request=request)
        # Act
        with patch.object(Minio, "__init__", return_value=None), patch("boto3.client", return_value=None):
            zip_storage_repo = ZipStorageRepo(organization_id=organization_id, workspace_id=workspace_id)

        # Assert
        assert zip_storage_repo.s3_workspace_root == os.path.join(
            "organizations",
            str(organization_id),
            "workspaces",
            str(workspace_id),
        )
