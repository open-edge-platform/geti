# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pydantic
import pytest
from geti_configuration_tools.training_configuration import PartialTrainingConfiguration

from communication.views.training_configuration_rest_views import TrainingConfigurationRESTViews


class TestTrainingConfigurationRESTViews:
    def test_training_configuration_from_rest(self) -> None:
        # Arrange - Create a sample REST view of a training configuration
        training_config_rest = {
            "task_id": "detection_1",
            "model_manifest_id": "model_manifest_123",
            "training": [
                {"key": "max_epochs", "value": 100, "type": "int", "name": "Epochs"},
                {"key": "learning_rate", "value": 0.042, "type": "float", "name": "Learning rate"},
                {"early_stopping": {"enable": True, "patience": 5}},
            ],
            "evaluation": [],
        }

        # Act - Convert from REST to TrainingConfiguration
        result = TrainingConfigurationRESTViews.training_configuration_from_rest(training_config_rest)

        # Assert
        assert isinstance(result, PartialTrainingConfiguration)
        assert result.task_id == "detection_1"
        assert result.model_manifest_id == "model_manifest_123"

        # Check hyperparameters
        assert hasattr(result, "hyperparameters")
        assert hasattr(result.hyperparameters, "training")
        assert result.hyperparameters.training.max_epochs == 100
        assert result.hyperparameters.training.early_stopping.enable
        assert result.hyperparameters.training.early_stopping.patience == 5
        assert result.hyperparameters.training.learning_rate == 0.042

    def test_training_configuration_to_rest(
        self, fxt_training_configuration_task_level, fxt_training_configuration_task_level_rest_view
    ) -> None:
        rest_view = TrainingConfigurationRESTViews.training_configuration_to_rest(fxt_training_configuration_task_level)
        assert rest_view == fxt_training_configuration_task_level_rest_view

    def test_training_configuration_from_rest_empty_configs(self) -> None:
        """Test converting a training configuration from REST with empty configs."""
        # Arrange
        training_config_rest = {
            "task_id": "detection_1",
        }

        # Act
        result = TrainingConfigurationRESTViews.training_configuration_from_rest(training_config_rest)

        # Assert
        assert isinstance(result, PartialTrainingConfiguration)
        assert result.task_id == "detection_1"
        assert hasattr(result, "global_parameters")
        assert hasattr(result, "hyperparameters")

    def test_training_configuration_from_rest_missing_fields(self) -> None:
        """Test converting a training configuration from REST without optional fields."""
        # Arrange - Only include task_id, which is required
        training_config_rest = {
            "task_id": "detection_1",
        }

        # Act
        result = TrainingConfigurationRESTViews.training_configuration_from_rest(training_config_rest)

        # Assert
        assert isinstance(result, PartialTrainingConfiguration)
        assert result.task_id == "detection_1"
        assert hasattr(result, "global_parameters")
        assert hasattr(result, "hyperparameters")

    @pytest.mark.parametrize(
        "rest_input",
        [
            # Missing required task_id
            {
                "dataset_preparation": {},
                "training": [],
            },
            # Invalid parameter type
            {
                "task_id": "detection_1",
                "training": [
                    {"key": "max_epochs", "value": "not_an_integer", "type": "int"},
                    {"key": "non_existing param", "value": "not_an_integer", "type": "int"},
                ],
            },
            # Invalid subset split (sum != 100)
            {
                "task_id": "detection_1",
                "dataset_preparation": {
                    "subset_split": {
                        "training": 80,
                        "validation": 30,
                        "test": 10,
                    },
                },
            },
        ],
        ids=[
            "missing_task_id",
            "invalid_parameter_type",
            "invalid_subset_split",
        ],
    )
    def test_training_configuration_from_rest_validation(self, rest_input) -> None:
        """Test validation errors when converting invalid REST inputs."""
        # Act & Assert
        with pytest.raises(pydantic.ValidationError):
            TrainingConfigurationRESTViews.training_configuration_from_rest(rest_input)

    def test_training_configuration_bidirectional_conversion(
        self, fxt_training_configuration_task_level, fxt_training_configuration_task_level_rest_view
    ) -> None:
        rest_view = TrainingConfigurationRESTViews.training_configuration_to_rest(fxt_training_configuration_task_level)

        assert rest_view == fxt_training_configuration_task_level_rest_view

        training_configuration = TrainingConfigurationRESTViews.training_configuration_from_rest(rest_view)

        assert training_configuration.model_dump() == fxt_training_configuration_task_level.model_dump()
