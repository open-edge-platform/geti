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

import pytest
from testfixtures import compare

from communication.constants import MAX_N_MEDIA_RETURNED
from communication.controllers.active_learning_controller import ActiveLearningController
from communication.exceptions import WorkspaceNotFoundException

from geti_types import ID

DUMMY_ORGANIZATION_ID = "000000000000000000000001"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_TASK_ID = "234567890123456789010009"

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"
API_ACTIVE_SET_PATTERN = f"{API_PROJECT_PATTERN}/datasets/active"

DUMMY_USER = ID("dummy_user")


@pytest.fixture
def fxt_active_set_rest():
    yield {"active_set": [{"MOCK_IMAGE_REST_KEY": "MOCK_IMAGE_REST_VALUE"}]}


class TestActiveLearningRESTEndpoint:
    @pytest.mark.parametrize(
        "limit, task_id",
        [
            (1, None),
            (MAX_N_MEDIA_RETURNED + 1, DUMMY_TASK_ID),
        ],
    )
    def test_active_set_endpoint_get(self, fxt_director_app, fxt_active_set_rest, limit, task_id) -> None:
        endpoint = f"{API_ACTIVE_SET_PATTERN}?limit={limit}"
        if task_id:
            endpoint += f"&task_id={task_id}"

        with patch.object(
            ActiveLearningController,
            "get_active_set",
            return_value=fxt_active_set_rest,
        ) as mock_get_active_set:
            result = fxt_director_app.get(endpoint)

        mock_get_active_set.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            limit=min(limit, MAX_N_MEDIA_RETURNED),
            user_id=DUMMY_USER,
            task_id=ID(task_id) if task_id else None,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), fxt_active_set_rest, ignore_eq=True)

    def test_active_set_endpoint_get_invalid_limit(
        self,
        fxt_director_app,
    ) -> None:
        limit = "dummy_limit"
        endpoint = f"{API_ACTIVE_SET_PATTERN}?limit={limit}"

        result = fxt_director_app.get(endpoint)

        assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_active_set_endpoint_workspace_not_found(self, fxt_director_app, fxt_active_set_rest) -> None:
        with patch.object(
            ActiveLearningController,
            "get_active_set",
            side_effect=WorkspaceNotFoundException(ID(DUMMY_WORKSPACE_ID)),
        ) as mock_model_test_results:
            result = fxt_director_app.get(API_ACTIVE_SET_PATTERN)

        assert result.status_code == HTTPStatus.NOT_FOUND
        mock_model_test_results.assert_called_once()
