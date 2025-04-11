# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
from unittest.mock import patch
from urllib.parse import urlencode

import pytest
from starlette import status
from starlette.testclient import TestClient
from testfixtures import compare

from microservice.rest.job_controller import JobController
from microservice.rest.main import app

from geti_fastapi_tools.dependencies import get_source_fastapi, get_user_id_fastapi
from geti_types import ID, RequestSource
from sc_sdk.utils.time_utils import now

DUMMY_ORGANIZATION_ID = "000000000000000000000001"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_JOB_ID = "923857474846573626510000"
DUMMY_DATA = {"dummy_key": "dummy_value"}
DUMMY_USER = "dummy_user"

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_JOBS_PATTERN = f"{API_WORKSPACE_PATTERN}/jobs"


def patched_user() -> ID:
    return ID("dummy_user")


@pytest.fixture(scope="function")
def fxt_client() -> TestClient:
    """Test client for FastAPI app."""
    app.dependency_overrides[get_user_id_fastapi] = patched_user
    app.dependency_overrides[get_source_fastapi] = lambda: RequestSource.UNKNOWN
    return TestClient(app)


class TestJobRESTEndpoint:
    def test_job_endpoint_get(self, fxt_client) -> None:
        # Arrange
        endpoint = f"{API_JOBS_PATTERN}/{DUMMY_JOB_ID}"

        # Act
        with patch.object(JobController, "get_job", return_value=DUMMY_DATA) as mock_get_job_by_id:
            result = fxt_client.get(endpoint)

        # Assert
        mock_get_job_by_id.assert_called_once_with(
            job_id=ID(DUMMY_JOB_ID),
            user_uid=DUMMY_USER,
        )
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_job_endpoint_cancel(self, fxt_client) -> None:
        # Arrange
        endpoint = f"{API_JOBS_PATTERN}/{DUMMY_JOB_ID}:cancel"
        dummy_response = "Job marked as cancelled"

        # Act
        with patch.object(JobController, "cancel_job", return_value=dummy_response) as mock_cancel_job:
            result = fxt_client.post(endpoint)

        mock_cancel_job.assert_called_once_with(
            job_id=ID(DUMMY_JOB_ID),
            user_uid=DUMMY_USER,
        )
        assert result.status_code == status.HTTP_202_ACCEPTED
        assert json.loads(result.content) == dummy_response

    def test_job_endpoint_delete(self, fxt_client) -> None:
        # Arrange
        endpoint = f"{API_JOBS_PATTERN}/{DUMMY_JOB_ID}"
        dummy_response = "Job marked as deleted"

        # Act
        with patch.object(JobController, "cancel_job", return_value=dummy_response) as mock_cancel_job:
            result = fxt_client.delete(endpoint)

        mock_cancel_job.assert_called_once_with(
            job_id=ID(DUMMY_JOB_ID),
            user_uid=DUMMY_USER,
            delete_job=True,
        )
        assert result.status_code == status.HTTP_202_ACCEPTED
        assert json.loads(result.content) == dummy_response

    def test_jobs_endpoint(self, fxt_client) -> None:
        # Arrange
        project_id = "234567890123456789010000"
        state = "SUBMITTED"
        job_type_1 = "train"
        job_type_2 = "optimize"
        key = "{'key': 'value}"
        author_id = "author_id"
        start_time_from = now()
        start_time_to = now()
        skip = 1
        limit = 10
        sort_by = "start_time"
        sort_direction = "desc"
        query = {
            "project_id": project_id,
            "state": state,
            "key": key,
            "author_id": author_id,
            "start_time_from": start_time_from.isoformat(),
            "start_time_to": start_time_to.isoformat(),
            "skip": skip,
            "limit": limit,
            "sort_by": sort_by,
            "sort_direction": sort_direction,
        }
        endpoint = f"{API_JOBS_PATTERN}?job_type={job_type_1}&job_type={job_type_2}&{urlencode(query)}"

        # Act
        with patch.object(JobController, "get_jobs", return_value=DUMMY_DATA) as mock_get_jobs:
            result = fxt_client.get(endpoint, headers={"x-auth-request-access-token": "testing"})

        # Assert
        mock_get_jobs.assert_called_once_with(
            user_id=DUMMY_USER,
            project_id=ID(project_id),
            state=state,
            job_types=[job_type_1, job_type_2],
            key=key,
            author_uid=author_id,
            start_time_from=start_time_from,
            start_time_to=start_time_to,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)
