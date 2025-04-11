# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

import json
from http import HTTPStatus
from unittest.mock import patch

import numpy as np
import pytest

from communication.controllers.training_controller import TrainingController

from geti_types import ID

DUMMY_ORGANIZATION_ID = "567890123456789012340001"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_DATASET_ID = "184377438465364732664000"
DUMMY_IMAGE_ID = "624738256723562375620000"
DUMMY_VIDEO_ID = "835463642801460237560000"
DUMMY_MAPS_ID = "390491047582734283004100"
DUMMY_FRAME_ID = "123"
DUMMY_DATA = {"dummy_key": "dummy_value"}
DUMMY_MEDIA_BINARY = np.full((10, 10, 3), 255)

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"

API_TRAIN_PATTERN = f"{API_PROJECT_PATTERN}:train"
API_TRAIN_PATTERN_LEGACY = f"{API_PROJECT_PATTERN}/train"

DUMMY_USER = ID("dummy_user")


def do_nothing(self, *args, **kwargs) -> None:
    return None


class TestTrainingRESTEndpoint:
    @pytest.mark.parametrize(
        "endpoint_path",
        [API_TRAIN_PATTERN, API_TRAIN_PATTERN_LEGACY],
        ids=[":train", "/train (legacy)"],
    )
    def test_train_endpoint(self, fxt_director_app, endpoint_path) -> None:
        request_data = DUMMY_DATA
        dummy_job_rest = {"dummy_job_rest_key": "dummy_job_rest_value"}

        with patch.object(TrainingController, "train_task", return_value=dummy_job_rest) as mock_train_task:
            result = fxt_director_app.post(endpoint_path, json=request_data)

        mock_train_task.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID), raw_train_config=DUMMY_DATA, author=DUMMY_USER
        )
        assert result.status_code == HTTPStatus.OK
        assert json.loads(result.content) == dummy_job_rest

    def test_train_endpoint_no_payload(self, fxt_director_app) -> None:
        dummy_job_rest = {"dummy_job_rest_key": "dummy_job_rest_value"}
        with patch.object(TrainingController, "train_task", return_value=dummy_job_rest) as mock_train_task:
            result = fxt_director_app.post(API_TRAIN_PATTERN)
        mock_train_task.assert_called_once_with(project_id=ID(DUMMY_PROJECT_ID), raw_train_config={}, author=DUMMY_USER)
        assert result.status_code == HTTPStatus.OK
        assert json.loads(result.content) == dummy_job_rest

    @pytest.mark.parametrize(
        "endpoint_path",
        [API_TRAIN_PATTERN_LEGACY, API_TRAIN_PATTERN],
        ids=["/train (legacy)", ":train"],
    )
    def test_train_endpoint_deprecated_headers(self, fxt_director_app, endpoint_path) -> None:
        """
        Tests if the headers are added correctly when the deprecated endpoint is used.
        """
        dummy_job_rest = {"dummy_job_rest_key": "dummy_job_rest_value"}
        with patch.object(TrainingController, "train_task", return_value=dummy_job_rest):
            result = fxt_director_app.post(endpoint_path)
            # Check if the Deprecation and Warning headers are added
        if endpoint_path == API_TRAIN_PATTERN_LEGACY:
            assert "Deprecation" in result.headers
            assert "Sunset" in result.headers
            assert "Link" in result.headers
        else:
            assert "Deprecation" not in result.headers
            assert "Sunset" not in result.headers
            assert "Link" not in result.headers
