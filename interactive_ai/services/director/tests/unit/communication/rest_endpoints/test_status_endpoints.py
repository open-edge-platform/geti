# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from http import HTTPStatus
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.controllers.status_controller import StatusController

DUMMY_ORGANIZATION_ID = "567890123456789012340001"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"
API_INCREMENTAL_LEARNING_STATUS_PATTERN = f"{API_PROJECT_PATTERN}/incremental_learning_status"


@pytest.fixture
def fxt_incremental_learning_status_rest():
    yield {"MOCK_IMAGE_REST_KEY": "MOCK_IMAGE_REST_VALUE"}


class TestStatusEndpoints:
    def test_incremental_learning_status_endpoint(self, fxt_director_app, fxt_incremental_learning_status_rest) -> None:
        with patch.object(
            StatusController,
            "get_incremental_learning_status",
            return_value=fxt_incremental_learning_status_rest,
        ) as mock_get_status:
            result = fxt_director_app.get(API_INCREMENTAL_LEARNING_STATUS_PATTERN)

        assert result.status_code == HTTPStatus.OK
        mock_get_status.assert_called_once()
        compare(
            json.loads(result.content),
            fxt_incremental_learning_status_rest,
            ignore_eq=True,
        )

    def test_organization_status_endpoint(self, fxt_director_app) -> None:
        endpoint = f"{API_ORGANIZATION_PATTERN}/status"
        dummy_result = {"n_running_jobs": 1}
        with patch.object(StatusController, "get_server_status", return_value=dummy_result):
            result = fxt_director_app.get(endpoint)

        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), dummy_result, ignore_eq=True)
