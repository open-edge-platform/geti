# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
        mock_installation_profile = "standard"

        # Act
        with (
            patch.dict(
                os.environ,
                {
                    "PLATFORM_VERSION": mock_platform_version,
                    "BUILD_VERSION": mock_build_version,
                    "INTEL_EMAIL": mock_intel_email,
                    "INSTALLATION_PROFILE": mock_installation_profile,
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
            "installation-profile": mock_installation_profile,
        }

        # Act
        with (
            patch.dict(
                os.environ,
                {
                    "PLATFORM_VERSION": mock_platform_version,
                    "BUILD_VERSION": mock_build_version,
                    "INTEL_EMAIL": mock_intel_email,
                    "INSTALLATION_PROFILE": mock_installation_profile,
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
            "installation-profile": mock_installation_profile,
        }

    def test_sc_product_info_endpoint_project_file_not_found(self, fxt_resource_rest):
        # Arrange
        mock_platform_version = "1.2.3"
        mock_build_version = "1.2.3-unittest"
        mock_intel_email = "test@intel.com"
        endpoint = "/api/v1/product_info"
        mock_installation_profile = "standard"

        # Act
        # Test that when the smtp_host file is not found, no exception is raised
        with (
            patch.dict(
                os.environ,
                {
                    "PLATFORM_VERSION": mock_platform_version,
                    "BUILD_VERSION": mock_build_version,
                    "INTEL_EMAIL": mock_intel_email,
                    "INSTALLATION_PROFILE": mock_installation_profile,
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
            "installation-profile": mock_installation_profile,
        }
