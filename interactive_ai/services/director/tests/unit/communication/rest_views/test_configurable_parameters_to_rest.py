# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from communication.views.configurable_parameters_to_rest import ConfigurableParametersRESTViews


class TestConfigurableParametersFromRest:
    """Test suite for the configurable_parameters_from_rest method."""

    def test_simple_parameters_list(self):
        """Test converting a list of simple parameters from REST format."""
        # Arrange
        rest_input = [
            {"key": "min_images_per_label", "value": 5, "type": "int", "name": "Minimum images per label"},
            {"key": "enable", "value": True, "type": "bool", "name": "Enable auto training"},
            {"key": "threshold", "value": 0.75, "type": "float", "name": "Confidence threshold"},
        ]

        expected_output = {
            "min_images_per_label": 5,
            "enable": True,
            "threshold": 0.75,
        }

        # Act
        result = ConfigurableParametersRESTViews.configurable_parameters_from_rest(rest_input)

        # Assert
        assert result == expected_output

    def test_nested_dictionary(self):
        """Test converting a nested dictionary from REST format."""
        # Arrange
        rest_input = {
            "training": {
                "constraints": [
                    {"key": "min_images_per_label", "value": 10, "type": "int"},
                ]
            },
            "auto_training": [
                {"key": "enable", "value": True, "type": "bool"},
                {"key": "min_images_per_label", "value": 5, "type": "int"},
            ],
        }

        expected_output = {
            "training": {
                "constraints": {
                    "min_images_per_label": 10,
                }
            },
            "auto_training": {
                "enable": True,
                "min_images_per_label": 5,
            },
        }

        # Act
        result = ConfigurableParametersRESTViews.configurable_parameters_from_rest(rest_input)

        # Assert
        assert result == expected_output

    def test_mixed_content(self):
        """Test converting a mixed list containing both parameters and nested structures."""
        # Arrange
        rest_input = [
            {"key": "task_id", "value": "detection_1", "type": "str"},
            {
                "training": [
                    {"key": "epochs", "value": 50, "type": "int"},
                ],
                "auto_training": [
                    {"key": "enable", "value": True, "type": "bool"},
                ],
            },
        ]

        expected_output = {
            "task_id": "detection_1",
            "training": {
                "epochs": 50,
            },
            "auto_training": {
                "enable": True,
            },
        }

        # Act
        result = ConfigurableParametersRESTViews.configurable_parameters_from_rest(rest_input)

        # Assert
        assert result == expected_output

    def test_empty_inputs(self):
        """Test with empty inputs."""
        # Empty list
        assert ConfigurableParametersRESTViews.configurable_parameters_from_rest([]) == {}

        # Empty dict
        assert ConfigurableParametersRESTViews.configurable_parameters_from_rest({}) == {}

    def test_non_dict_list_input(self):
        """Test with non-dictionary, non-list input."""
        # String input should be returned as is
        assert ConfigurableParametersRESTViews.configurable_parameters_from_rest("test") == "test"

        # Number input should be returned as is
        assert ConfigurableParametersRESTViews.configurable_parameters_from_rest(42) == 42
