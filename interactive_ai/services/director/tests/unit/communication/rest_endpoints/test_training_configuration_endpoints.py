# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from http import HTTPStatus
from unittest.mock import patch

from testfixtures import compare

from communication.controllers.training_configuration_controller import TrainingConfigurationRESTController
from features.feature_flag_provider import FeatureFlag

from geti_types import ID, ProjectIdentifier

DUMMY_ORGANIZATION_ID = "000000000000000000000001"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"


class TestTrainingConfigurationEndpoints:
    def test_get_training_configuration(
        self, fxt_director_app, fxt_training_configuration_task_level, fxt_enable_feature_flag_name
    ) -> None:
        # Arrange
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS.name)
        fxt_training_configuration_task_level.model_manifest_id = "dummy_model_manifest_id"
        dummy_rest_view = {"dummy_key": "dummy_value"}
        project_identifier = ProjectIdentifier(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
        )
        task_id = fxt_training_configuration_task_level.task_id
        model_manifest_id = fxt_training_configuration_task_level.model_manifest_id
        endpoint_url = (
            f"{API_PROJECT_PATTERN}/training_configuration?"
            f"task_id={str(task_id)}&model_manifest_id={model_manifest_id}&exclude_none=true"
        )

        # Act
        with patch.object(
            TrainingConfigurationRESTController,
            "get_configuration",
            return_value=dummy_rest_view,
        ) as mock_get_training_config:
            result = fxt_director_app.get(endpoint_url)

        # Assert
        mock_get_training_config.assert_called_once_with(
            project_identifier=project_identifier,
            task_id=task_id,
            model_manifest_id=model_manifest_id,
            model_id=None,
        )

        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), dummy_rest_view, ignore_eq=True)

    def test_get_project_configuration_feature_flag_off(self, fxt_director_app) -> None:
        # check that endpoint is not available when feature flag is off
        result = fxt_director_app.get(f"{API_PROJECT_PATTERN}/training_configuration")

        assert result.status_code == HTTPStatus.FORBIDDEN
