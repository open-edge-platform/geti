# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json

from models.user import User
from models.user_settings import UserSettings, UserSettingsResponse


def test_get_user_settings(user: User, organization, signed_token: str):
    settings = json.dumps({"test": "a"})
    user_settings = UserSettings(user_id=user.id, organization_id=organization.id, settings=settings)
    response: UserSettingsResponse = user_settings.create(headers={"x-auth-request-access-token": signed_token})

    user_settings = UserSettings.get(headers={"x-auth-request-access-token": signed_token})

    assert user_settings.settings == settings
    assert response.message == "User settings successfully created"


def test_get_user_settings_fail_missing_project_id(user: User, organization, signed_token: str):
    # create with project id
    settings = json.dumps({"test": "PROJECT ID PASSED IN CREATE"})
    user_settings = UserSettings(
        user_id=user.id,
        organization_id=organization.id,
        settings=settings,
        project_id="a79d51e2-b43c-453a-b22f-86c9621f17f1",
    )
    user_settings.create(headers={"x-auth-request-access-token": signed_token})

    # we are trying to get user_settings without project_id - it should return no content
    response = UserSettings.get(headers={"x-auth-request-access-token": signed_token})

    assert response is None


def test_get_user_settings_for_project_id(user: User, organization, signed_token: str):
    # create without project id
    settings = json.dumps({"test": "no project id"})
    user_settings = UserSettings(user_id=user.id, organization_id=organization.id, settings=settings)
    response: UserSettingsResponse = user_settings.create(headers={"x-auth-request-access-token": signed_token})
    assert response.message == "User settings successfully created"

    # create with project id
    settings2 = json.dumps({"test": "PROJECT ID PASSED IN CREATE"})
    user_settings.project_id = "a79d51e2-b43c-453a-b22f-86c9621f17f1"
    user_settings.settings = settings2
    response2: UserSettingsResponse = user_settings.create(headers={"x-auth-request-access-token": signed_token})
    assert response2.message == "User settings successfully created"

    # assert no project id
    user_settings = UserSettings.get(headers={"x-auth-request-access-token": signed_token})
    assert user_settings.settings == settings

    user_settings = UserSettings.get(
        headers={"x-auth-request-access-token": signed_token}, project_id="a79d51e2-b43c-453a-b22f-86c9621f17f1"
    )
    assert user_settings.settings == settings2


def test_get_user_settings_no_content(signed_token: str):
    response = UserSettings.get(headers={"x-auth-request-access-token": signed_token})

    assert response is None
