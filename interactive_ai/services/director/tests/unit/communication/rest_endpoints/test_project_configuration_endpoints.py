# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from http import HTTPStatus
from unittest.mock import patch

from testfixtures import compare

from communication.controllers.project_configuration_controller import ProjectConfigurationRESTController
from features.feature_flag_provider import FeatureFlag

from geti_types import ID, ProjectIdentifier

DUMMY_ORGANIZATION_ID = "000000000000000000000001"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"


class TestProjectConfigurationEndpoints:
    def test_get_project_configuration(
        self, fxt_director_app, fxt_project_configuration, fxt_enable_feature_flag_name
    ) -> None:
        # Arrange
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS.name)
        project_config_dict = fxt_project_configuration.model_dump()
        project_identifier = ProjectIdentifier(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
        )

        # Act
        with patch.object(
            ProjectConfigurationRESTController,
            "get_configuration",
            return_value=project_config_dict,
        ) as mock_get_project_config:
            result = fxt_director_app.get(f"{API_PROJECT_PATTERN}/project_configuration")

        # Assert
        mock_get_project_config.assert_called_once_with(project_identifier=project_identifier)

        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), project_config_dict, ignore_eq=True)

    def test_feature_flag_off(self, fxt_director_app) -> None:
        # check that endpoints are not available when feature flag is off
        result = fxt_director_app.get(f"{API_PROJECT_PATTERN}/project_configuration")

        assert result.status_code == HTTPStatus.FORBIDDEN

        result = fxt_director_app.patch(
            f"{API_PROJECT_PATTERN}/project_configuration",
            json={"some": "configuration"},
        )

        assert result.status_code == HTTPStatus.FORBIDDEN

    def test_update_project_configuration(
        self, fxt_director_app, fxt_project_configuration, fxt_enable_feature_flag_name
    ) -> None:
        # Arrange
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS.name)
        project_config_dict = fxt_project_configuration.model_dump()
        project_identifier = ProjectIdentifier(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
        )

        # Act
        with patch.object(
            ProjectConfigurationRESTController,
            "update_configuration",
            return_value=None,
        ) as mock_update_project_config:
            result = fxt_director_app.patch(
                f"{API_PROJECT_PATTERN}/project_configuration",
                json=project_config_dict,
            )

        # Assert
        mock_update_project_config.assert_called_once_with(
            project_identifier=project_identifier,
            project_configuration=mock_update_project_config.call_args[1]["project_configuration"],
        )
        assert result.status_code == HTTPStatus.NO_CONTENT
        assert not result.content  # 204 responses must not include a response body
