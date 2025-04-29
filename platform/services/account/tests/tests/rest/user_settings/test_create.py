# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http
import json

import pytest
from models.error import AccountServiceError
from models.user import User
from models.user_settings import UserSettings, UserSettingsResponse


def test_create_user_settings_no_project_id(user: User, organization, signed_token: str):
    settings = json.dumps({"test": "a"})
    user_settings = UserSettings(user_id=user.id, organization_id=organization.id, settings=settings)
    response: UserSettingsResponse = user_settings.create(headers={"x-auth-request-access-token": signed_token})

    assert response.message != ""


def test_create_and_modify_user_settings(user: User, organization, signed_token: str):
    create_request_settings = json.dumps({"test": "a"})
    update_request_settings = json.dumps({"test": "b"})

    user_settings = UserSettings(user_id=user.id, organization_id=organization.id, settings=create_request_settings)
    create_response: UserSettingsResponse = user_settings.create(headers={"x-auth-request-access-token": signed_token})
    created_settings: UserSettings = UserSettings.get(headers={"x-auth-request-access-token": signed_token})

    user_settings.settings = update_request_settings
    update_response: UserSettingsResponse = user_settings.create(headers={"x-auth-request-access-token": signed_token})
    updated_settings: UserSettings = UserSettings.get(headers={"x-auth-request-access-token": signed_token})

    assert create_response.message == "User settings successfully created"
    assert created_settings.settings == create_request_settings

    assert update_response.message == "User settings successfully updated"
    assert updated_settings.settings == update_request_settings


def test_create_user_settings_payload_too_big(user: User, organization, signed_token: str):
    settings = json.dumps({"test": "a" * 3000})
    user_settings = UserSettings(user_id=user.id, organization_id=organization.id, settings=settings)

    with pytest.raises(AccountServiceError) as err:
        user_settings.create(headers={"x-auth-request-access-token": signed_token})

    assert err.value.message == "Settings provided exceed the maximum of 3000 characters"
    assert err.value.status_code == http.HTTPStatus.BAD_REQUEST
