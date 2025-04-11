# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
from http import HTTPStatus
from unittest.mock import mock_open, patch


class TestProductInfoRESTEndpoint:
    def test_sc_product_info_endpoint_project(self, fxt_resource_rest):
        # Arrange
        mock_platform_version = "1.2.3"
        mock_build_version = "1.2.3-unittest"
        mock_smtp_host = "10.10.10.10"
        mock_intel_email = "test@intel.com"
        endpoint = "/api/v1/product_info"

        # Act
        with (
            patch.dict(
                os.environ,
                {
                    "PLATFORM_VERSION": mock_platform_version,
                    "BUILD_VERSION": mock_build_version,
                    "INTEL_EMAIL": mock_intel_email,
                },
            ),
            patch(
                "communication.rest_endpoints.product_info_endpoints.open",
                mock_open(read_data=""),
            ) as mocked_open_smtp,
            patch(
                "communication.rest_endpoints.product_info_endpoints.is_grafana_enabled",
                side_effect=[False],
            ),
            patch(
                "communication.rest_endpoints.product_info_endpoints.get_environment",
                side_effect=["on-prem"],
            ),
            patch(
                "communication.rest_endpoints.product_info_endpoints.get_gpu_provider",
                side_effect=["intel"],
            ),
        ):
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mocked_open_smtp.assert_called_once_with("/mnt/smtp_server_secret/smtp_host")
        assert result.status_code == HTTPStatus.OK
        assert result.json() == {
            "product-version": mock_platform_version,
            "build-version": mock_build_version,
            "intel-email": mock_intel_email,
            "smtp-defined": "False",
            "grafana_enabled": False,
            "environment": "on-prem",
            "gpu-provider": "intel",
        }

        # Act
        with (
            patch.dict(
                os.environ,
                {
                    "PLATFORM_VERSION": mock_platform_version,
                    "BUILD_VERSION": mock_build_version,
                    "INTEL_EMAIL": mock_intel_email,
                },
            ),
            patch(
                "communication.rest_endpoints.product_info_endpoints.open",
                mock_open(read_data=mock_smtp_host),
            ) as mocked_open_smtp,
            patch(
                "communication.rest_endpoints.product_info_endpoints.is_grafana_enabled",
                side_effect=[True],
            ),
            patch(
                "communication.rest_endpoints.product_info_endpoints.get_environment",
                side_effect=["saas"],
            ),
            patch(
                "communication.rest_endpoints.product_info_endpoints.get_gpu_provider",
                side_effect=["none"],
            ),
        ):
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mocked_open_smtp.assert_called_once_with("/mnt/smtp_server_secret/smtp_host")
        assert result.status_code == HTTPStatus.OK
        assert result.json() == {
            "product-version": mock_platform_version,
            "build-version": mock_build_version,
            "intel-email": mock_intel_email,
            "smtp-defined": "True",
            "grafana_enabled": True,
            "environment": "saas",
            "gpu-provider": "none",
        }

    def test_sc_product_info_endpoint_project_file_not_found(self, fxt_resource_rest):
        # Arrange
        mock_platform_version = "1.2.3"
        mock_build_version = "1.2.3-unittest"
        mock_intel_email = "test@intel.com"
        endpoint = "/api/v1/product_info"

        # Act
        # Test that when the smtp_host file is not found, no exception is raised
        with (
            patch.dict(
                os.environ,
                {
                    "PLATFORM_VERSION": mock_platform_version,
                    "BUILD_VERSION": mock_build_version,
                    "INTEL_EMAIL": mock_intel_email,
                },
            ),
            patch(
                "communication.rest_endpoints.product_info_endpoints.open",
                side_effect=FileNotFoundError(),
            ) as mocked_open_smtp,
            patch(
                "communication.rest_endpoints.product_info_endpoints.is_grafana_enabled",
                side_effect=[True],
            ),
            patch(
                "communication.rest_endpoints.product_info_endpoints.get_environment",
                side_effect=["on-prem"],
            ),
            patch(
                "communication.rest_endpoints.product_info_endpoints.get_gpu_provider",
                side_effect=["nvidia"],
            ),
        ):
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mocked_open_smtp.assert_called_once()
        assert result.status_code == HTTPStatus.OK
        assert result.json() == {
            "product-version": mock_platform_version,
            "build-version": mock_build_version,
            "smtp-defined": "False",
            "intel-email": mock_intel_email,
            "grafana_enabled": True,
            "environment": "on-prem",
            "gpu-provider": "nvidia",
        }
