# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import copy

import sc_sdk.configuration.elements.metadata_keys as metadata_keys
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.enums.config_element_type import ConfigElementType
from tests.configuration.dummy_config import DatasetManagerConfig

from geti_types import ID


class TestConfigurableParameters:
    def test_configurable_parameters(self):
        """
        <b>Description:</b>
        Check "ConfigurableParameters" class object initialization

        <b>Input data:</b>
        "ConfigurableParameters" class object with specified initialization parameters

        <b>Expected results:</b>
        Test passes if attributes of initialized "ConfigurableParameters" class object are equal to expected
        """

        def check_configurable_parameters_attributes(
            configurable_parameters: ConfigurableParameters,
            expected_header: str,
            expected_description: str,
            expected_id: ID,
            expected_visible_in_ui: bool,
        ):
            assert configurable_parameters.header == expected_header
            assert configurable_parameters.description == expected_description
            assert configurable_parameters.type == ConfigElementType.CONFIGURABLE_PARAMETERS
            assert configurable_parameters.groups == []
            assert configurable_parameters.id == expected_id
            assert configurable_parameters.visible_in_ui == expected_visible_in_ui

        header = "Test Header"
        # Checking "ConfigurableParameters" initialized with default optional parameters
        check_configurable_parameters_attributes(
            configurable_parameters=ConfigurableParameters(header=header),
            expected_header=header,
            expected_description="Default parameter group description",
            expected_id=ID(""),
            expected_visible_in_ui=True,
        )
        # Checking "ConfigurableParameters" initialized with specified optional parameters
        description = "Test Description"
        config_id = ID("Test ID")
        visible_in_ui = False
        check_configurable_parameters_attributes(
            configurable_parameters=ConfigurableParameters(
                header=header,
                description=description,
                id=config_id,
                visible_in_ui=visible_in_ui,
            ),
            expected_header=header,
            expected_description=description,
            expected_id=config_id,
            expected_visible_in_ui=visible_in_ui,
        )

    def test_set_metadata(self):
        """
        <b>Description:</b>
        Check "ConfigurableParameters" class parameter metadata setting

        <b>Input data:</b>
        Dummy configuration -- DatasetManagerConfig

        <b>Expected results:</b>
        Test passes if:
            1. Metadata for a given parameter inside the ConfigurableParameters can be
               set successfully,
            2. Attempting to set metadata for a non-existing parameter results in
               failure
            3. Attempting to set metadata for a non-existing metadata key results in
               failure
            4. Attempting to set metadata to a value of a type that does not match the
               original metadata item type results in failure
            5. Resetting the metadata back to its original value can be done
               successfully
        """
        # Arrange
        config = DatasetManagerConfig(
            description="Configurable parameters for the DatasetManager -- TEST ONLY",
            header="Dataset Manager configuration -- TEST ONLY",
        )
        test_parameter_name = "dummy_float_selectable"
        metadata_key = metadata_keys.EDITABLE
        old_value = config.get_metadata(test_parameter_name)[metadata_key]
        new_value = False

        # Act
        success = config.set_metadata_value(
            parameter_name=test_parameter_name,
            metadata_key=metadata_key,
            value=new_value,
        )
        no_success_invalid_param = config.set_metadata_value(
            parameter_name=test_parameter_name + "_invalid",
            metadata_key=metadata_key,
            value=new_value,
        )
        no_success_invalid_key = config.set_metadata_value(
            parameter_name=test_parameter_name,
            metadata_key=metadata_key + "_invalid",
            value=new_value,
        )
        no_success_invalid_value_type = config.set_metadata_value(
            parameter_name=test_parameter_name,
            metadata_key=metadata_key,
            value=str(new_value),
        )
        config_copy = copy.deepcopy(config)
        success_revert = config_copy.set_metadata_value(
            parameter_name=test_parameter_name,
            metadata_key=metadata_key,
            value=old_value,
        )

        # Assert
        assert old_value != new_value
        assert all([success, success_revert])
        assert not any(
            [
                no_success_invalid_key,
                no_success_invalid_param,
                no_success_invalid_value_type,
            ]
        )
        assert config.get_metadata(test_parameter_name)[metadata_key] == new_value
        assert config_copy.get_metadata(test_parameter_name)[metadata_key] == old_value
