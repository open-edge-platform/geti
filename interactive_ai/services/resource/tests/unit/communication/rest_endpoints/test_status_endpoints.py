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

from testfixtures import compare

from communication.exceptions import FailedHealthCheck

from geti_fastapi_tools.responses import success_response_rest

API_PATTERN = "/healthz"


class TestStatusEndpoint:
    def test_health_check_resource_endpoint_success(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_PATTERN}?mongodb=true&kafka=false"
        success_rest = success_response_rest()

        # Act
        with patch("communication.rest_endpoints.status_endpoints.health_check") as mock_health_check:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_health_check.assert_called_once_with(mongodb_check=True, kafka_check=False)
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), success_rest, ignore_eq=True)

    def test_health_check_resource_endpoint_server_error(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_PATTERN}?mongodb=true"
        dummy_exception_message = "dummy_ex_msg"
        error_rest = {"detail": f"{dummy_exception_message}"}

        # Act
        with patch(
            "communication.rest_endpoints.status_endpoints.health_check",
            side_effect=FailedHealthCheck(dummy_exception_message),
        ) as mock_health_check:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_health_check.assert_called_once_with(mongodb_check=True, kafka_check=False)
        assert result.status_code == 500
        compare(result.json(), error_rest, ignore_eq=True)
