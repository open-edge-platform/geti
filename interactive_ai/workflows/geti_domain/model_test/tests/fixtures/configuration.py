# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from attr import attrs
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.configuration.elements.default_model_parameters import DefaultModelParameters
from iai_core.configuration.elements.hyper_parameters import HyperParameters
from iai_core.configuration.elements.parameter_group import ParameterGroup, add_parameter_group
from iai_core.configuration.elements.primitive_parameters import (
    configurable_boolean,
    configurable_integer,
    float_selectable,
    string_attribute,
)


@pytest.fixture
def fxt_configurable_parameters_1():
    @attrs
    class DummyParametersOne(ConfigurableParameters):
        header = string_attribute("Dummy Configuration")
        description = string_attribute("Some description")
        dummy_parameter = configurable_integer(default_value=2, header="Dummy integer", min_value=-10, max_value=10)

    yield DummyParametersOne()


@pytest.fixture
def fxt_configuration_1(fxt_mongo_id, fxt_configurable_parameters_1):
    yield HyperParameters(
        workspace_id=fxt_mongo_id(1),
        project_id=fxt_mongo_id(2),
        model_storage_id=fxt_mongo_id(3),
        id_=fxt_mongo_id(4),
        data=fxt_configurable_parameters_1,
    )


@pytest.fixture
def fxt_configuration(fxt_configuration_1):
    yield fxt_configuration_1


@pytest.fixture
def fxt_hyper_parameters_with_groups(fxt_model_storage, fxt_mongo_id):
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
        workspace_id=fxt_mongo_id(0),
        project_id=fxt_mongo_id(1),
        model_storage_id=fxt_model_storage.id_,
        id_=fxt_mongo_id(2),
        data=DummyHyperParameters(),
    )
