# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from _pytest.fixtures import FixtureRequest
from attr import attrib, attrs

from tests.test_helpers import add_hyper_parameters_to_template, register_model_template

from iai_core_py.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core_py.configuration.elements.parameter_group import ParameterGroup, add_parameter_group
from iai_core_py.configuration.elements.primitive_parameters import configurable_integer, string_attribute
from iai_core_py.entities.model_template import ModelTemplate


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
