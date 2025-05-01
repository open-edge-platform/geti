# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from sc_sdk.configuration.elements.component_parameters import ComponentParameters, ComponentType
from sc_sdk.configuration.elements.entity_identifiers import ComponentEntityIdentifier, ModelEntityIdentifier
from sc_sdk.configuration.elements.hyper_parameters import HyperParameters

from geti_types import ID


class TestConfigurationElements:
    def test_configurations_entity_identifier(self) -> None:
        """
        <b>Description:</b>
        This test verifies that the entity_identifier returns a correct view of the identifying properties of
        configurations.

        <b>Input data:</b>
        Dummy IDs created in the test

        <b>Expected results:</b>
        Test passes if the identifying IDs and types are correctly stored in the entity identifier for TaskConfig,
        ModelConfig and ComponentConfig

        <b>Steps</b>
        1. Create dummy ComponentParameters and HyperParameters
        2. Assert the respective entity_identifiers match the expected values
        3. Assert that the entity_identifier is correctly converted to a dictionary using the as_dict() method
        4. Assert that the entity_identifier is updated when the configuration identifiers change
        """
        workspace_id = ID("12345678")
        project_id = ID("123456789")
        model_storage_id = ID("1234567")
        component = ComponentType.DATASET_COUNTER
        cp: ComponentParameters = ComponentParameters(
            workspace_id=workspace_id,
            project_id=project_id,
            component=component,
            id_=ID("component_param_id"),
        )
        hp: HyperParameters = HyperParameters(
            workspace_id=workspace_id,
            project_id=project_id,
            model_storage_id=model_storage_id,
            id_=ID("hyper_param_id"),
        )

        assert hp.entity_identifier.model_storage_id == model_storage_id

        assert cp.entity_identifier.component == component
        assert cp.entity_identifier.task_id == ID()

        assert cp.entity_identifier.as_dict()["component"] == component
        assert hp.entity_identifier.as_dict()["model_storage_id"] == model_storage_id

        new_workspace_id = ID("87654321")
        new_project_id = ID("987654321")

        hp.workspace_id = new_workspace_id

        cp.project_id = new_project_id
        cp.workspace_id = new_workspace_id

        expected_cc_entity_identifier = ComponentEntityIdentifier(
            project_id=new_project_id,
            task_id=ID(),
            component=component,
            workspace_id=new_workspace_id,
        )
        assert cp.entity_identifier == expected_cc_entity_identifier

        expected_mc_entity_identifier = ModelEntityIdentifier(
            workspace_id=new_workspace_id,
            project_id=project_id,
            model_storage_id=model_storage_id,
        )
        assert hp.entity_identifier == expected_mc_entity_identifier
