# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pydantic
import pytest
from geti_configuration_tools.project_configuration import PartialProjectConfiguration

from communication.views.project_configuration_rest_views import ProjectConfigurationRESTViews


class TestProjectConfigurationRESTViews:
    def test_project_configuration_from_rest(self):
        """Test converting a project configuration from REST to a ProjectConfiguration object."""
        # Arrange - Create a sample REST view of a project configuration
        project_config_rest = {
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
                        {
                            "key": "enable_dynamic_required_annotations",
                            "value": True,
                            "type": "bool",
                            "name": "Enable dynamic required annotations",
                        },
                    ],
                },
                {
                    "task_id": "classification_1",
                    "training": {
                        "constraints": [
                            {
                                "key": "min_images_per_label",
                                "value": 20,
                                "type": "int",
                                "name": "Minimum images per label",
                            }
                        ]
                    },
                    "auto_training": [
                        {"key": "enable", "value": True, "type": "bool", "name": "Enable auto training"},
                        {"key": "min_images_per_label", "value": 10, "type": "int", "name": "Minimum images per label"},
                        {
                            "key": "enable_dynamic_required_annotations",
                            "value": False,
                            "type": "bool",
                            "name": "Enable dynamic required annotations",
                        },
                    ],
                },
            ]
        }

        # Act - Convert from REST to ProjectConfiguration
        result = ProjectConfigurationRESTViews.project_configuration_from_rest(project_config_rest)

        # Assert
        assert isinstance(result, PartialProjectConfiguration)
        assert len(result.task_configs) == 2

        # Check first task config
        task1 = result.task_configs[0]
        assert task1.task_id == "detection_1"
        assert task1.training.constraints.min_images_per_label == 15
        assert task1.auto_training.enable is False
        assert task1.auto_training.min_images_per_label == 8
        assert task1.auto_training.enable_dynamic_required_annotations is True

        # Check second task config
        task2 = result.task_configs[1]
        assert task2.task_id == "classification_1"
        assert task2.training.constraints.min_images_per_label == 20
        assert task2.auto_training.enable is True
        assert task2.auto_training.min_images_per_label == 10
        assert task2.auto_training.enable_dynamic_required_annotations is False

    def test_project_configuration_from_rest_empty_task_configs(self):
        """Test converting a project configuration from REST with empty task_configs."""
        # Arrange
        project_config_rest = {"task_configs": []}

        # Act
        result = ProjectConfigurationRESTViews.project_configuration_from_rest(project_config_rest)

        # Assert
        assert isinstance(result, PartialProjectConfiguration)
        assert len(result.task_configs) == 0

    def test_project_configuration_from_rest_missing_task_configs(self):
        """Test converting a project configuration from REST without task_configs field."""
        # Arrange
        project_config_rest = {}

        # Act
        result = ProjectConfigurationRESTViews.project_configuration_from_rest(project_config_rest)

        # Assert
        assert isinstance(result, PartialProjectConfiguration)
        assert len(result.task_configs) == 0

    def test_project_configuration_from_rest_malformed_task_config(self):
        """Test converting a project configuration from REST with malformed task config."""
        # Arrange - Missing required fields in task config
        project_config_rest = {
            "task_configs": [
                {
                    "task_id": "detection_1",
                    # missing training field
                    "auto_training": [
                        {"key": "enable", "value": False, "type": "bool"},
                    ],
                }
            ]
        }

        # Act & Assert
        # The function should handle missing fields by creating a model with default values
        result = ProjectConfigurationRESTViews.project_configuration_from_rest(project_config_rest)

        # Should still create a valid model with default values for missing fields
        assert isinstance(result, PartialProjectConfiguration)
        assert len(result.task_configs) == 1
        assert result.task_configs[0].task_id == "detection_1"
        assert result.task_configs[0].auto_training.enable is False
        # Training field should use default values since it was missing
        assert hasattr(result.task_configs[0], "training")

    @pytest.mark.parametrize(
        "rest_input",
        [
            {"another_unknown_field": "should be ignored"},
            {
                "task_configs": [{"task_id": "detection_1", "unknown_field": "this field doesn't exist in the model"}],
            },
            {
                "task_configs": [
                    {
                        "task_id": "detection_1",
                        "auto_training": [
                            {"key": "unknown_field", "value": True},
                        ],
                    }
                ],
            },
            {
                "task_configs": [
                    {
                        "task_id": "detection_1",
                        "training": {
                            "constraints": [
                                {
                                    "key": "min_images_per_label",
                                    "value": "not_an_integer",  # String instead of int
                                    "type": "int",
                                }
                            ]
                        },
                    }
                ]
            },
        ],
        ids=[
            "unknown_top_level_field",
            "unknown_task_config_field",
            "unknown_auto_training_parameter",
            "invalid_value_type",
        ],
    )
    def test_project_configuration_from_rest_validation(self, rest_input):
        # Act
        with pytest.raises(pydantic.ValidationError):
            ProjectConfigurationRESTViews.project_configuration_from_rest(rest_input)
