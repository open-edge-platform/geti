# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from attr import attrs

from coordination.dataset_manager.subset_manager_config import SubsetManagerConfig

from geti_types import ID
from sc_sdk.configuration.elements.component_parameters import ComponentParameters, ComponentType
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.default_model_parameters import DefaultModelParameters
from sc_sdk.configuration.elements.entity_identifiers import ComponentEntityIdentifier, ModelEntityIdentifier
from sc_sdk.configuration.elements.hyper_parameters import HyperParameters
from sc_sdk.configuration.elements.parameter_group import ParameterGroup, add_parameter_group
from sc_sdk.configuration.elements.primitive_parameters import (
    configurable_boolean,
    configurable_float,
    configurable_integer,
    float_selectable,
    string_attribute,
)

WORKSPACE_ID = ID("workspace_id")


@pytest.fixture
def fxt_configurable_parameters_1():
    @attrs
    class DummyParametersOne(ConfigurableParameters):
        header = string_attribute("Dummy Configuration")
        description = string_attribute("Some description")
        dummy_parameter = configurable_integer(default_value=2, header="Dummy integer", min_value=-10, max_value=10)

    yield DummyParametersOne()


@pytest.fixture
def fxt_configurable_parameters_2():
    @attrs
    class DummyParametersTwo(ConfigurableParameters):
        header = string_attribute("Another Configuration")
        description = string_attribute("Another description")
        dummy_parameter = configurable_float(default_value=0.5, header="Dummy float", min_value=0, max_value=1)

    yield DummyParametersTwo()


@pytest.fixture
def fxt_configuration_1(
    fxt_mongo_id,
    fxt_configurable_parameters_1,
    fxt_project,
    fxt_model_storage,
):
    yield HyperParameters(
        workspace_id=WORKSPACE_ID,
        project_id=fxt_project.id_,
        model_storage_id=fxt_model_storage.id_,
        id_=fxt_mongo_id(1),
        data=fxt_configurable_parameters_1,
    )


@pytest.fixture
def fxt_configuration_2(fxt_mongo_id, fxt_configurable_parameters_2, fxt_project):
    yield ComponentParameters(
        workspace_id=WORKSPACE_ID,
        project_id=fxt_project.id_,
        id_=fxt_mongo_id(1),
        component=ComponentType.DATASET_COUNTER,
        data=fxt_configurable_parameters_2,
    )


@pytest.fixture
def fxt_subset_manager_config(fxt_mongo_id, fxt_project):
    yield ComponentParameters(
        workspace_id=WORKSPACE_ID,
        id_=fxt_mongo_id(1),
        project_id=fxt_project.id_,
        task_id=fxt_mongo_id(2),
        component=ComponentType.SUBSET_MANAGER,
        data=SubsetManagerConfig(header="123"),
    )


@pytest.fixture
def fxt_configuration(fxt_configuration_1):
    yield fxt_configuration_1


@pytest.fixture
def fxt_model_entity_identifier_dict(fxt_project, fxt_model_storage):
    yield {
        "type": "HYPER_PARAMETERS",
        "workspace_id": str(WORKSPACE_ID),
        "model_storage_id": str(fxt_model_storage.id_),
        "project_id": str(fxt_project.id_),
    }


@pytest.fixture
def fxt_model_entity_identifier(fxt_project, fxt_model_storage):
    yield ModelEntityIdentifier(
        workspace_id=WORKSPACE_ID,
        project_id=fxt_project.id_,
        model_storage_id=fxt_model_storage.id_,
    )


@pytest.fixture
def fxt_component_entity_identifier(fxt_project):
    yield ComponentEntityIdentifier(
        workspace_id=WORKSPACE_ID,
        project_id=fxt_project.id_,
        task_id=ID(),
        component=ComponentType.DATASET_COUNTER,
    )


@pytest.fixture
def fxt_component_entity_identifier_dict(fxt_project):
    yield {
        "type": "COMPONENT_PARAMETERS",
        "component": "DATASET_COUNTER",
        "task_id": "",
        "workspace_id": str(WORKSPACE_ID),
        "project_id": str(fxt_project.id_),
    }


@pytest.fixture
def fxt_configuration_rest_1(fxt_mongo_id, fxt_model_entity_identifier_dict):
    yield {
        "id": str(fxt_mongo_id(1)),
        "header": "Dummy Configuration",
        "description": "Some description",
        "type": "CONFIGURABLE_PARAMETERS",
        "entity_identifier": fxt_model_entity_identifier_dict,
        "parameters": [
            {
                "data_type": "integer",
                "default_value": 2,
                "description": "Default integer description",
                "editable": True,
                "header": "Dummy integer",
                "max_value": 10,
                "min_value": -10,
                "name": "dummy_parameter",
                "template_type": "input",
                "ui_rules": {},
                "value": 2,
                "warning": None,
            }
        ],
    }


@pytest.fixture
def fxt_configuration_rest_2(fxt_mongo_id, fxt_component_entity_identifier_dict):
    yield {
        "id": str(fxt_mongo_id(1)),
        "header": "Another Configuration",
        "description": "Another description",
        "type": "CONFIGURABLE_PARAMETERS",
        "entity_identifier": fxt_component_entity_identifier_dict,
        "parameters": [
            {
                "data_type": "float",
                "default_value": 0.5,
                "description": "Default float description",
                "editable": True,
                "header": "Dummy float",
                "max_value": 1,
                "min_value": 0,
                "step_size": None,
                "name": "dummy_parameter",
                "template_type": "input",
                "ui_rules": {},
                "value": 0.5,
                "warning": None,
            }
        ],
    }


@pytest.fixture
def fxt_configuration_rest(fxt_configuration_rest_1):
    yield fxt_configuration_rest_1


@pytest.fixture
def fxt_configuration_rest_restructured_1(fxt_mongo_id):
    yield {
        "id": str(fxt_mongo_id(1)),
        "header": "Dummy Configuration",
        "description": "Some description",
        "type": "CONFIGURABLE_PARAMETERS",
        "dummy_parameter": {
            "data_type": "integer",
            "default_value": 2,
            "description": "Default integer description",
            "editable": True,
            "header": "Dummy integer",
            "max_value": 10,
            "min_value": -10,
            "template_type": "input",
            "value": 2,
            "warning": None,
        },
    }


@pytest.fixture
def fxt_configuration_rest_restructured_2(fxt_mongo_id):
    yield {
        "id": str(fxt_mongo_id(1)),
        "header": "Another Configuration",
        "description": "Another description",
        "type": "CONFIGURABLE_PARAMETERS",
        "dummy_parameter": {
            "data_type": "float",
            "default_value": 0.5,
            "description": "Default float description",
            "editable": True,
            "header": "Dummy float",
            "max_value": 1,
            "min_value": 0,
            "step_size": None,
            "template_type": "input",
            "value": 0.5,
            "warning": None,
        },
    }


@pytest.fixture
def fxt_configuration_rest_restructured(fxt_configuration_rest_restructured_1):
    yield fxt_configuration_rest_restructured_1


@pytest.fixture
def fxt_default_model_hyper_parameters(fxt_model_storage, fxt_mongo_id, fxt_project):
    yield HyperParameters(
        workspace_id=fxt_project.workspace_id,
        project_id=fxt_project.id_,
        model_storage_id=fxt_model_storage.id_,
        data=DefaultModelParameters(),
        id_=fxt_mongo_id(1),
    )


@pytest.fixture
def fxt_default_model_hyper_parameters_data():
    yield {
        "learning_parameters": {
            "batch_size": {"value": 4},
            "epochs": {"value": 10},
            "learning_rate": {"value": 0.001},
        }
    }


@pytest.fixture
def fxt_hyper_parameters_with_groups(fxt_model_storage, fxt_mongo_id, fxt_project):
    @attrs
    class DummyHyperParameters(DefaultModelParameters):
        @attrs
        class _DummyGroup(ParameterGroup):
            header = string_attribute("Dummy parameter group")
            dummy_float_selectable = float_selectable(
                default_value=2.0,
                options=[1.0, 1.5, 2.0],
                header="Dummy float selectable",
            )
            dummy_boolean = configurable_boolean(
                header="Dummy boolean",
                default_value=True,
            )

        dummy_group = add_parameter_group(_DummyGroup)

    yield HyperParameters(
        workspace_id=fxt_project.workspace_id,
        project_id=fxt_project.id_,
        model_storage_id=fxt_model_storage.id_,
        data=DummyHyperParameters(),
        id_=fxt_mongo_id(1),
    )


@pytest.fixture
def fxt_hyperparameters(fxt_model_storage, fxt_mongo_id, fxt_project):
    @attrs
    class DummyOptParameters(DefaultModelParameters):
        @attrs
        class _POTOptimization(ParameterGroup):
            header = string_attribute("pot parameter group")
            stat_subset_size = configurable_integer(
                default_value=300,
                header="Dummy integer",
                min_value=1,
                max_value=9223372036854775807,
            )

        pot_parameters = add_parameter_group(_POTOptimization)

    yield HyperParameters(
        workspace_id=fxt_project.workspace_id,
        project_id=fxt_project.id_,
        model_storage_id=fxt_model_storage.id_,
        data=DummyOptParameters(),
        id_=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_pot_hyperparameters(fxt_model_storage, fxt_mongo_id, fxt_project):
    @attrs
    class DummyPOTParameters(DefaultModelParameters):
        @attrs
        class _POTOptimization(ParameterGroup):
            header = string_attribute("pot parameter group")
            stat_subset_size = configurable_integer(
                default_value=300,
                header="Dummy integer",
                min_value=1,
                max_value=9223372036854775807,
            )

        pot_parameters = add_parameter_group(_POTOptimization)

    yield HyperParameters(
        workspace_id=fxt_project.workspace_id,
        project_id=fxt_project.id_,
        model_storage_id=fxt_model_storage.id_,
        data=DummyPOTParameters(),
        id_=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_default_learning_parameters_rest_response(fxt_mongo_id):
    yield {
        "description": "Parameters to control basic training behavior.",
        "header": "Learning Parameters",
        "name": "learning_parameters",
        "id": fxt_mongo_id(1) + "-1",
        "parameters": [
            {
                "data_type": "integer",
                "default_value": 4,
                "description": "The number of training samples seen in each "
                "iteration of training. Setting this higher "
                "will make the training more stable, but will "
                "require more memory. Setting this lower will "
                "make the training less stable, but will "
                "require less memory.",
                "editable": True,
                "header": "Batch size",
                "max_value": 1000,
                "min_value": 1,
                "name": "batch_size",
                "template_type": "input",
                "ui_rules": {},
                "value": 4,
                "warning": "Increasing this value may cause the system to use "
                "more memory than available, potentially causing "
                "out of memory errors, please update with "
                "caution.",
            },
            {
                "data_type": "integer",
                "default_value": 10,
                "description": "Increasing this value causes the results to "
                "be more robust but training time will be "
                "longer.",
                "editable": True,
                "header": "Number of epochs",
                "max_value": 10000,
                "min_value": 1,
                "name": "epochs",
                "template_type": "input",
                "ui_rules": {},
                "value": 10,
                "warning": None,
            },
            {
                "data_type": "float",
                "default_value": 0.001,
                "description": "Increasing this value will speed up training convergence but might make it unstable.",
                "editable": True,
                "header": "Learning rate",
                "max_value": 10000000000.0,
                "min_value": 1e-30,
                "name": "learning_rate",
                "step_size": None,
                "template_type": "input",
                "ui_rules": {},
                "value": 0.001,
                "warning": None,
            },
        ],
        "type": "PARAMETER_GROUP",
    }


@pytest.fixture
def fxt_dummy_parameter_group_rest_response(fxt_mongo_id):
    yield {
        "description": "Default parameter group description",
        "header": "Dummy parameter group",
        "name": "dummy_group",
        "id": fxt_mongo_id(1) + "-0",
        "parameters": [
            {
                "data_type": "boolean",
                "default_value": True,
                "description": "Default configurable boolean description",
                "editable": True,
                "header": "Dummy boolean",
                "name": "dummy_boolean",
                "template_type": "input",
                "ui_rules": {},
                "value": True,
                "warning": None,
            },
            {
                "data_type": "float",
                "default_value": 2.0,
                "description": "Default selectable description",
                "editable": True,
                "header": "Dummy float selectable",
                "name": "dummy_float_selectable",
                "options": [1.0, 1.5, 2.0],
                "template_type": "selectable",
                "ui_rules": {},
                "value": 2.0,
                "warning": None,
            },
        ],
        "type": "PARAMETER_GROUP",
    }


@pytest.fixture
def fxt_hyper_parameter_group_entity_identifier_rest(fxt_model_storage, fxt_project):
    def generate_hparam_group_entity_identifier(group_name: str):
        """
        Returns a hyper parameter group entity identifier with the group name set
        """
        return {
            "workspace_id": str(fxt_project.workspace_id),
            "project_id": str(fxt_project.id_),
            "model_storage_id": str(fxt_model_storage.id_),
            "type": "HYPER_PARAMETER_GROUP",
            "group_name": group_name,
        }

    yield generate_hparam_group_entity_identifier


@pytest.fixture
def fxt_default_learning_parameters_rest_request(
    fxt_hyper_parameter_group_entity_identifier_rest,
):
    yield {
        "entity_identifier": fxt_hyper_parameter_group_entity_identifier_rest(group_name="learning_parameters"),
        "parameters": [
            {
                "name": "batch_size",
                "value": 4,
            },
            {
                "name": "epochs",
                "value": 10,
            },
            {
                "name": "learning_rate",
                "value": 0.001,
            },
        ],
        "type": "PARAMETER_GROUP",
    }


@pytest.fixture
def fxt_dummy_parameter_group_rest_request(
    fxt_hyper_parameter_group_entity_identifier_rest,
):
    yield {
        "entity_identifier": fxt_hyper_parameter_group_entity_identifier_rest(group_name="dummy_group"),
        "parameters": [
            {
                "name": "dummy_boolean",
                "value": True,
            },
            {
                "name": "dummy_float_selectable",
                "value": 2.0,
            },
        ],
        "type": "PARAMETER_GROUP",
    }


@pytest.fixture
def fxt_hyper_parameters_with_groups_rest_request_restructured():
    yield {
        "learning_parameters": {
            "type": "PARAMETER_GROUP",
            "batch_size": {"value": 4},
            "epochs": {"value": 10},
            "learning_rate": {"value": 0.001},
        },
        "dummy_group": {
            "type": "PARAMETER_GROUP",
            "dummy_boolean": {"value": True},
            "dummy_float_selectable": {"value": 2.0},
        },
    }


@pytest.fixture
def fxt_component_parameters(fxt_component_entity_identifier):
    yield ComponentParameters.from_entity_identifier(
        fxt_component_entity_identifier,
        id=ID("fxt_component_parameters_id"),
        data=ConfigurableParameters(header="Empty component parameters"),
    )
