# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from rest.endpoints.install import install_platform
from rest.schema.install import InstallRequest


@pytest.fixture
def mock_environment(mocker):
    mocker.patch.dict(os.environ, {"REGISTRY": "test-registry", "VERSION": "2.11.0"})


@pytest.mark.parametrize(
    "version_number, expected_detail, expected_status",
    [
        ("2.11.0", "Installation of version 2.11.0 has started.", status.HTTP_200_OK),
        ("", "Version number is required.", status.HTTP_400_BAD_REQUEST),
        ("invalid_version", "Invalid version number provided.", status.HTTP_400_BAD_REQUEST),
    ],
)
def test_install_platform(mocker, mock_environment, version_number, expected_detail, expected_status):
    mocker.patch("rest.endpoints.install.load_kube_config")
    mocker.patch("rest.endpoints.install.check_config_map_exists", return_value=False)
    mocker.patch("rest.endpoints.install.create_service_account", return_value=MagicMock())
    mocker.patch("rest.endpoints.install.create_cluster_role", return_value=MagicMock())
    mocker.patch("rest.endpoints.install.create_cluster_role_binding", return_value=MagicMock())
    mocker.patch("rest.endpoints.install.deploy_service_account")
    mocker.patch("rest.endpoints.install.deploy_cluster_role")
    mocker.patch("rest.endpoints.install.deploy_cluster_role_binding")
    mocker.patch("rest.endpoints.install.create_job", return_value=MagicMock())
    mocker.patch("rest.endpoints.install.deploy_job")

    payload = InstallRequest(version_number=version_number)

    if expected_status == status.HTTP_200_OK:
        response = install_platform(payload)
        assert response.detail == expected_detail
    else:
        with pytest.raises(HTTPException) as e:
            install_platform(payload)
        assert e.value.status_code == expected_status
        assert e.value.detail == expected_detail


def test_install_platform_already_installed(mocker, mock_environment):
    mocker.patch("rest.endpoints.install.load_kube_config")
    mocker.patch("rest.endpoints.install.check_config_map_exists", return_value=True)

    payload = InstallRequest(version_number="2.9.0")

    with pytest.raises(HTTPException) as e:
        install_platform(payload)

    assert e.value.status_code == status.HTTP_409_CONFLICT
    assert e.value.detail == "Platform is already installed."
