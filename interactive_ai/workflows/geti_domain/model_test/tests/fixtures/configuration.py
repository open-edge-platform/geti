# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import pytest
from attr import attrs
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.default_model_parameters import DefaultModelParameters
from sc_sdk.configuration.elements.hyper_parameters import HyperParameters
from sc_sdk.configuration.elements.parameter_group import ParameterGroup, add_parameter_group
from sc_sdk.configuration.elements.primitive_parameters import (
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
