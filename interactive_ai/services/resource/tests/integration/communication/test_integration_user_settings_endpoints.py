# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from communication.constants import MAX_SETTINGS_LENGTH_IN_CHARACTERS
from communication.exceptions import NoUserSettingsException, SettingsTooLongException
from repos.ui_settings_repo import UISettingsRepo

from geti_fastapi_tools.exceptions import BadRequestException


class TestUserSettingsEndpoints:
    @pytest.mark.parametrize("with_project", [False, True], ids=["with_project", "without_project"])
    def test_user_settings_endpoint(
        self,
        request,
        fxt_resource_rest,
        fxt_mongo_id,
        with_project,
    ) -> None:
        """
        Tests the setting and getting of the per user per project settings. Also checks
        if the correct response is returned when they are not found. Settings are set
        twice to see if they correctly overwrite when new settings are saved.
        """
        project_id = fxt_mongo_id(123)
        request.addfinalizer(lambda: UISettingsRepo()._collection.delete_many({}))

        if with_project:
            endpoint = f"/api/v1/user_settings?project_id={str(project_id)}"
        else:
            endpoint = "/api/v1/user_settings"

        test_settings = {"settings": {"setting_1": "value_1", "setting_2": "etc"}}
        test_settings2 = {"settings": {"setting_2": "value_2", "setting_3": "etc"}}

        # get settings (there should be none)
        response = fxt_resource_rest.get(endpoint)
        assert response.status_code == NoUserSettingsException().http_status, response.json()

        # create settings
        post_result = fxt_resource_rest.post(endpoint, json=test_settings)
        assert post_result.status_code == 200

        # get settings (now they should be available)
        settings_response = fxt_resource_rest.get(endpoint)
        assert settings_response.status_code == 200
        assert settings_response.json()["settings"] == str(test_settings["settings"])

        # update settings
        post_result = fxt_resource_rest.post(endpoint, json=test_settings2)
        assert post_result.status_code == 200

        # get settings (should have updated values)
        settings_response2 = fxt_resource_rest.get(endpoint)
        assert settings_response2.json()["settings"] == str(test_settings2["settings"])

    def test_user_settings_endpoint_settings_too_long(
        self,
        fxt_resource_rest,
    ) -> None:
        # Test with too long 'settings' parameter in the REST payload
        endpoint = "/api/v1/user_settings"
        long_setting = "_dummy" * MAX_SETTINGS_LENGTH_IN_CHARACTERS
        request_data: dict = {"settings": long_setting}
        response = fxt_resource_rest.post(endpoint, json=request_data)
        assert response.status_code == SettingsTooLongException(MAX_SETTINGS_LENGTH_IN_CHARACTERS).http_status

    def test_user_settings_endpoint_no_settings(
        self,
        fxt_resource_rest,
    ) -> None:
        # Test with no 'settings' parameter in the REST payload
        endpoint = "/api/v1/user_settings"
        request_data: dict = {}

        response = fxt_resource_rest.post(endpoint, json=request_data)
        assert response.status_code == BadRequestException.http_status
