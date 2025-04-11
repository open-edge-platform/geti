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
from http import HTTPStatus
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.constants import MAX_N_MEDIA_RETURNED
from communication.rest_controllers import MediaScoreRESTController
from usecases.dataset_filter import DatasetFilterSortDirection, MediaScoreFilterField

from geti_fastapi_tools.exceptions import BadRequestException
from geti_types import ID

DUMMY_DATA = {"dummy_key": "dummy_value"}
DUMMY_TEST_ID = "012345678901234567890000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_ORGANIZATION_ID = "567890123456789012340200"

API_BASE_PATTERN = (
    f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
    f"/workspaces/{DUMMY_WORKSPACE_ID}"
    f"/projects/{DUMMY_PROJECT_ID}"
    f"/tests/{DUMMY_TEST_ID}"
)


class TestMediaScoreRESTEndpoint:
    @pytest.mark.parametrize(
        "limit, skip, sort_dir",
        [
            (1, 1, "asc"),
            (MAX_N_MEDIA_RETURNED, 2, "dsc"),
        ],
    )
    def test_media_scores_filter_endpoint(self, fxt_resource_rest, limit, skip, sort_dir) -> None:
        # Arrange
        skip = 1
        request_data: dict = {"dummy_key": "value"}
        endpoint = f"{API_BASE_PATTERN}/results:query?limit={limit}&skip={skip}&sort_direction={sort_dir}"

        # Act
        with patch.object(
            MediaScoreRESTController,
            "get_filtered_items",
            return_value=DUMMY_DATA,
        ) as mock_get_filtered_items:
            result = fxt_resource_rest.post(endpoint, json=request_data)

        # Assert
        mock_get_filtered_items.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            model_test_result_id=ID(DUMMY_TEST_ID),
            sort_by=MediaScoreFilterField.SCORE,
            sort_direction=DatasetFilterSortDirection[sort_dir.upper()],
            limit=min(limit, MAX_N_MEDIA_RETURNED),
            skip=skip,
            query=request_data,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    @pytest.mark.parametrize(
        "limit, sort_by, sort_dir",
        [
            ("no_limit", "score", "asc"),
            (1, "score", "reverse"),
            (1, "label_id", "asc"),
            (1, "not_a_key", "asc"),
        ],
    )
    def test_media_scores_filter_endpoint_invalid_parameters(self, fxt_resource_rest, limit, sort_by, sort_dir) -> None:
        # Arrange
        request_data: dict = {"dummy_key": "value"}
        endpoint = f"{API_BASE_PATTERN}/results:query?limit={limit}&sort_by={sort_by}&sort_direction={sort_dir}"

        # Act and Assert
        response = fxt_resource_rest.post(endpoint, json=request_data)
        assert response.status_code == BadRequestException.http_status
