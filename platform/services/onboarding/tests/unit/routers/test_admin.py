# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_generate_onboarding_token() -> None:
    request_body = {
        "date_from": "2024-01-23",
        "date_to": "2044-01-01",
    }

    with patch("routers.admin.OnboardingTokenService") as token_service_mock:
        kms_token_svc = MagicMock()
        kms_token_svc.build_onboarding_token.return_value = "token_value_patch"
        token_service_mock.return_value = kms_token_svc
        response = client.post("/admin/onboarding/tokens", json=request_body)

        token_service_mock.assert_called_once()
        assert response.status_code == HTTPStatus.OK
        assert "onboarding_token" in response.json()


def test_generate_onboarding_token_fails_on_missing_secret() -> None:
    request_body = {
        "date_from": "2024-01-23",
        "date_to": "2044-01-01",
    }
    with patch("routers.admin.OnboardingTokenService") as token_service_mock:
        kms_token_svc = MagicMock()
        kms_token_svc.build_onboarding_token.side_effect = RuntimeError
        token_service_mock.return_value = kms_token_svc
        response = client.post("/admin/onboarding/tokens", json=request_body)

        token_service_mock.assert_called_once()
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.parametrize(
    "date_from, date_to",
    [
        ("2024-01-23", "2024-01-01"),
        ("03.07.2024", "10.07.2024"),
        (123, 567),
    ],
)
def test_generate_onboarding_token_fails_on_invalid_dates(date_from, date_to) -> None:
    request_body = {
        "date_from": date_from,
        "date_to": date_to,
    }
    with patch("routers.admin.OnboardingTokenService.build_onboarding_token", return_value="token_value_patch"):
        response = client.post("/admin/onboarding/tokens", json=request_body)

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
