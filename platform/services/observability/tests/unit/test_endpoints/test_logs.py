# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from urllib.parse import quote

import pytest
from endpoints.logs.logs import LogType, logs_endpoint
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from common.endpoint_validation import handle_request_validation_error
from common.telemetry import DateError
from common.utils import API_BASE_PATTERN

router = APIRouter(prefix=f"{API_BASE_PATTERN}/logs")
router.add_api_route(endpoint=logs_endpoint, path="/", methods=["GET"])
app = FastAPI()
app.add_exception_handler(RequestValidationError, handle_request_validation_error)
app.include_router(router)
client = TestClient(app)

_PATCHING_TARGET = "endpoints.logs.logs"


@pytest.mark.parametrize(
    "log_type_expected, start, end",
    (
        *[(elem, datetime(2020, 1, 1, tzinfo=timezone.utc), None) for elem in LogType],
        *[
            (elem, datetime(2020, 1, 1, tzinfo=timezone.utc), datetime(2022, 10, 14, tzinfo=timezone.utc))
            for elem in LogType
        ],
        (None, None, None),
    ),
)
def test_get_logs(mocker, tmp_path: Path, log_type_expected: LogType, start: datetime, end: datetime):
    """Tests the GET /logs method against valid requests."""
    file_name = "mock_log_archive.tar.gz"
    file_content = "Nobody expects the Spanish Inquisition!"
    path_file = tmp_path / file_name
    path_file.write_text(file_content)

    get_archive_mock = mocker.patch(f"{_PATCHING_TARGET}.get_telemetry_archive", return_value=path_file)

    params = []
    if log_type_expected:
        params.append(f"type={log_type_expected.value}")
    if start:
        params.append(f"start_date={quote(start.isoformat())}")
    if end:
        params.append(f"end_date={quote(end.isoformat())}")

    params_encoded = "&".join(params)
    path = f"{API_BASE_PATTERN}/logs?{params_encoded}"

    response = client.get(path)

    assert (
        response.status_code == HTTPStatus.OK
        and response.content == file_content.encode()
        and response.headers.get("content-type") == "application/octet-stream"
        and response.headers.get("content-disposition") == f'attachment; filename="{file_name}"'
    )
    get_archive_mock.assert_called_once_with(log_type=log_type_expected, start=start, end=end)


@pytest.mark.parametrize(
    "log_type", (pytest.param("", id="empty-str"), pytest.param("invalid", id="non-empty-invalid"))
)
def test_get_with_invalid_log_type(mocker, log_type: str):
    """Tests the GET /logs method against unsupported log types."""
    get_archive_mock = mocker.patch(f"{_PATCHING_TARGET}.get_telemetry_archive")

    response = client.get(f"{API_BASE_PATTERN}/logs?type={log_type}")

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    get_archive_mock.assert_not_called()


@pytest.mark.parametrize(
    "start, end",
    [
        pytest.param(datetime(2, 2, 2, tzinfo=timezone.utc), datetime(1, 1, 1, tzinfo=timezone.utc), id="far-apart"),
        pytest.param(datetime(1, 1, 2, tzinfo=timezone.utc), datetime(1, 1, 1, tzinfo=timezone.utc), id="diff-by-one"),
    ],
)
def test_get_with_invalid_datetime_range(mocker, start: datetime, end: datetime):
    """Tests the GET /logs method against invalid date ranges."""
    err_msg = "error message mock"
    get_archive_mock = mocker.patch(f"{_PATCHING_TARGET}.get_telemetry_archive", side_effect=[DateError(err_msg)])
    log_type_mock = LogType.K8S_LOGS

    path = f"{API_BASE_PATTERN}/logs?type={log_type_mock.value}&start_date={quote(start.isoformat())}&end_date={quote(end.isoformat())}"

    response = client.get(path)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY and response.json()["detail"] == err_msg
    get_archive_mock.assert_called_once_with(log_type=log_type_mock, start=start, end=end)
