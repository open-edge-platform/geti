# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from http import HTTPStatus
from unittest.mock import patch

import pytest
from geti_configuration_tools.training_configuration import PartialTrainingConfiguration
from testfixtures import compare

from communication.controllers.training_configuration_controller import TrainingConfigurationRESTController
from features.feature_flag import FeatureFlag

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

        result = fxt_director_app.patch(
            f"{API_PROJECT_PATTERN}/training_configuration",
            json={
                "task_id": "dummy_task_id",
                "model_manifest_id": "dummy_model_manifest_id",
            },
        )

        assert result.status_code == HTTPStatus.FORBIDDEN

    def test_update_training_configuration(self, fxt_director_app, fxt_enable_feature_flag_name) -> None:
        # Arrange
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS.name)

        # Create a sample REST input payload
        rest_input = {
            "task_id": "detection_1",
            "model_manifest_id": "model_manifest_123",
            "dataset_preparation": {
                "subset_split": {
                    "training": 70,
                    "validation": 20,
                    "test": 10,
                    "auto_selection": True,
                }
            },
            "training": [
                {"key": "max_epochs", "value": 100, "type": "int", "name": "Epochs"},
                {"key": "learning_rate", "value": 0.042, "type": "float", "name": "Learning rate"},
                {"early_stopping": {"enable": True, "patience": 5}},
            ],
            "evaluation": [],
        }

        # Act
        with patch.object(
            TrainingConfigurationRESTController,
            "update_configuration",
            return_value=None,
        ) as mock_update_training_config:
            result = fxt_director_app.patch(
                f"{API_PROJECT_PATTERN}/training_configuration",
                json=rest_input,
            )

        # Assert
        mock_update_training_config.assert_called_once()

        # Capture the update_configuration argument
        update_config = mock_update_training_config.call_args[1]["update_configuration"]

        # Verify it's a PartialTrainingConfiguration with expected values
        assert isinstance(update_config, PartialTrainingConfiguration)
        assert update_config.task_id == "detection_1"
        assert update_config.model_manifest_id == "model_manifest_123"

        # Check global parameters
        assert hasattr(update_config, "global_parameters")
        assert hasattr(update_config.global_parameters, "dataset_preparation")
        assert update_config.global_parameters.dataset_preparation.subset_split.training == 70
        assert update_config.global_parameters.dataset_preparation.subset_split.validation == 20
        assert update_config.global_parameters.dataset_preparation.subset_split.test == 10
        assert update_config.global_parameters.dataset_preparation.subset_split.auto_selection is True

        # Check hyperparameters
        assert hasattr(update_config, "hyperparameters")
        assert hasattr(update_config.hyperparameters, "training")
        assert update_config.hyperparameters.training.max_epochs == 100
        assert update_config.hyperparameters.training.learning_rate == 0.042
        assert update_config.hyperparameters.training.early_stopping.enable
        assert update_config.hyperparameters.training.early_stopping.patience == 5

        assert result.status_code == HTTPStatus.NO_CONTENT
        assert not result.content  # 204 responses must not include a response body

    @pytest.mark.parametrize(
        "payload, expected_error_type",
        [
            # Missing task_id
            (
                {
                    # missing task_id
                    "model_manifest_id": "model_manifest_123",
                    "dataset_preparation": {
                        "subset_split": {
                            "training": 70,
                            "validation": 20,
                            "test": 10,
                        }
                    },
                },
                "value_error",
            ),
            # Invalid data type
            (
                {
                    "task_id": "detection_1",
                    "model_manifest_id": "model_manifest_123",
                    "training": [{"key": "max_epochs", "value": "not_an_integer", "type": "int", "name": "Epochs"}],
                },
                "int_parsing",
            ),
            # Invalid split percentages (sum > 100)
            (
                {
                    "task_id": "detection_1",
                    "model_manifest_id": "model_manifest_123",
                    "dataset_preparation": {
                        "subset_split": {
                            "training": 70,
                            "validation": 20,
                            "test": 20,  # Total: 110%
                        }
                    },
                },
                "value_error",
            ),
            # Negative value error
            (
                {
                    "task_id": "detection_1",
                    "model_manifest_id": "model_manifest_123",
                    "training": [{"key": "learning_rate", "value": -0.01, "type": "float", "name": "Learning rate"}],
                },
                "greater_than",
            ),
        ],
        ids=[
            "missing_task_id",
            "invalid_data_type",
            "invalid_split_percentages",
            "negative_value",
        ],
    )
    def test_update_training_configuration_validation_errors(
        self, fxt_director_app, fxt_enable_feature_flag_name, payload, expected_error_type
    ) -> None:
        # Arrange
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS.name)

        # Act
        result = fxt_director_app.patch(
            f"{API_PROJECT_PATTERN}/training_configuration",
            json=payload,
        )

        # Assert
        assert result.status_code == HTTPStatus.BAD_REQUEST
        response = json.loads(result.content)
        assert "errors" in response
        assert len(response["errors"]) == 1
        assert response["errors"][0]["type"] == expected_error_type
