# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

from _pytest.fixtures import FixtureRequest
from attr import attrib, attrs

from tests.utils.test_helpers import add_hyper_parameters_to_template, register_model_template

from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.parameter_group import ParameterGroup, add_parameter_group
from sc_sdk.configuration.elements.primitive_parameters import configurable_integer, string_attribute
from sc_sdk.entities.model_template import ModelTemplate


@attrs
class MulticlassClassificationParameters(ConfigurableParameters):
    header: str = attrib(default="Dummy classification task configurable parameters")

    @attrs
    class __TaskParameters(ParameterGroup):
        header = string_attribute("Task parameters for a dummy classification task used in testing")
        description = header

        sleep_time = configurable_integer(
            header="Sleep time (in seconds)",
            default_value=10,
            min_value=0,
            max_value=100,
        )

    task_parameters = add_parameter_group(__TaskParameters)


class MultiClassClassification:
    """
    Mock classification task
    """


def register_classification_task(
    test_case: FixtureRequest,
) -> ModelTemplate:
    """Register MultiClassClassification task to model template list"""
    model_template_id = "mock/Classification"
    model_template = register_model_template(
        test_case,
        MultiClassClassification,
        model_template_id=model_template_id,
        model_template_path="",
        task_type="CLASSIFICATION",
        task_family="VISION",
        trainable=True,
    )
    add_hyper_parameters_to_template(model_template_id, MulticlassClassificationParameters)
    return model_template
