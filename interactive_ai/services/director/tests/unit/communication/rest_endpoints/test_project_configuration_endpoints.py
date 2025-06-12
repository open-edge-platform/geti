# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from http import HTTPStatus
from unittest.mock import patch

import pytest
from geti_configuration_tools.project_configuration import PartialProjectConfiguration
from testfixtures import compare

from communication.controllers.project_configuration_controller import ProjectConfigurationRESTController
from features.feature_flag import FeatureFlag

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
            json={},
        )

        assert result.status_code == HTTPStatus.FORBIDDEN

    def test_update_project_configuration(self, fxt_director_app, fxt_enable_feature_flag_name) -> None:
        # Arrange
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS.name)

        # Create a sample REST input payload
        rest_input = {
            "task_configs": [
                {
                    "task_id": "detection_1",
                    "training": {
                        "constraints": [
                            {
                                "key": "min_images_per_label",
                                "value": 15,
                                "type": "int",
                                "name": "Minimum images per label",
                            }
                        ]
                    },
                    "auto_training": [
                        {"key": "enable", "value": False, "type": "bool", "name": "Enable auto training"},
                        {"key": "min_images_per_label", "value": 8, "type": "int", "name": "Minimum images per label"},
                    ],
                }
            ]
        }

        # Act
        with patch.object(
            ProjectConfigurationRESTController,
            "update_configuration",
            return_value=None,
        ) as mock_update_project_config:
            result = fxt_director_app.patch(
                f"{API_PROJECT_PATTERN}/project_configuration",
                json=rest_input,
            )

        # Assert
        mock_update_project_config.assert_called_once()

        # Capture the update_configuration argument
        update_config = mock_update_project_config.call_args[1]["update_configuration"]

        # Verify it's a PartialProjectConfiguration with expected values
        assert isinstance(update_config, PartialProjectConfiguration)
        assert len(update_config.task_configs) == 1

        task_config = update_config.task_configs[0]
        assert task_config.task_id == "detection_1"
        assert task_config.training.constraints.min_images_per_label == 15
        assert task_config.auto_training.enable is False
        assert task_config.auto_training.min_images_per_label == 8

        assert result.status_code == HTTPStatus.NO_CONTENT
        assert not result.content  # 204 responses must not include a response body

    @pytest.mark.parametrize(
        "payload, expected_error_type",
        [
            # Missing task_id
            (
                {
                    "task_configs": [
                        {
                            # missing task_id
                            "training": {
                                "constraints": [
                                    {
                                        "key": "min_images_per_label",
                                        "value": 15,
                                        "type": "int",
                                        "name": "Minimum images per label",
                                    }
                                ]
                            }
                        }
                    ]
                },
                "value_error",
            ),
            # Invalid data type
            (
                {
                    "task_configs": [
                        {
                            "task_id": "detection_1",
                            "training": {
                                "constraints": [
                                    {
                                        "key": "min_images_per_label",
                                        "value": "not_an_integer",  # invalid type
                                        "type": "int",
                                        "name": "Minimum images per label",
                                    }
                                ]
                            },
                        }
                    ]
                },
                "int_parsing",
            ),
            # Invalid task_configs type
            (
                {
                    "task_configs": {  # should be a list
                        "task_id": "detection_1",
                    }
                },
                "model_type",
            ),
            # Invalid value (negative number)
            (
                {
                    "task_configs": [
                        {
                            "task_id": "detection_1",
                            "training": {
                                "constraints": [
                                    {
                                        "key": "min_images_per_label",
                                        "value": -5,  # invalid negative value
                                    }
                                ]
                            },
                        }
                    ]
                },
                "greater_than_equal",
            ),
        ],
        ids=[
            "missing_task_id",
            "invalid_data_type",
            "invalid_task_configs_type",
            "invalid_negative_value",
        ],
    )
    def test_update_project_configuration_validation_errors(
        self, fxt_director_app, fxt_enable_feature_flag_name, payload, expected_error_type
    ) -> None:
        # Arrange
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS.name)

        # Act
        result = fxt_director_app.patch(
            f"{API_PROJECT_PATTERN}/project_configuration",
            json=payload,
        )

        # Assert
        assert result.status_code == HTTPStatus.BAD_REQUEST
        response = json.loads(result.content)
        assert "errors" in response
        assert len(response["errors"]) == 1
        assert response["errors"][0]["type"] == expected_error_type
