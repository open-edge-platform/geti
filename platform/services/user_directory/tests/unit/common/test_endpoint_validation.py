"""
Unit tests for the common.endpoint_validation module.
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.exceptions import RequestValidationError

from common import endpoint_validation

if TYPE_CHECKING:
    from fastapi.responses import Response


@pytest.mark.asyncio
async def test_handle_request_validation_error():
    """Tests the handle_request_validation_error function."""
    req_method = "request method mock"
    req_url = "request url mock"

    request = Mock()
    request.method = req_method
    request.url = req_url

    error = Mock(RequestValidationError)

    with patch("common.endpoint_validation.logger") as logger_mock:
        logger_mock.error = Mock()

        response: Response = await endpoint_validation.handle_request_validation_error(request, error)

    assert (
        # Check the response.
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        and json.loads(response.body.decode())
        == {"code": status.HTTP_422_UNPROCESSABLE_ENTITY, "msg": "Request validation failed."}
        # Check logger calls.
        and logger_mock.error.call_count == 1
        and all(elem in logger_mock.error.call_args.args[0] for elem in [req_method, req_url, str(error)])
    )
