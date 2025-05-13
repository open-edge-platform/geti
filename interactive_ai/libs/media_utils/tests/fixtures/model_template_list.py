# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import iai_core.configuration.helper as otx_config_helper
import pytest
from _pytest.fixtures import FixtureRequest
from iai_core.algorithms import ModelTemplateList
from iai_core.configuration.elements.default_model_parameters import DefaultModelParameters
from iai_core.entities.model_template import (
    DatasetRequirements,
    HyperParameterData,
    InstantiationType,
    ModelTemplate,
    TaskFamily,
    TaskType,
)


@pytest.fixture(scope="class", autouse=True)
def fxt_register_dummy_model_templates(request: FixtureRequest):
    """
    This fixture provides dummy model templates (including hyper parameters) for all
    trainable tasks.
    """
    model_template_list = ModelTemplateList()
    hyper_parameters = HyperParameterData(base_path="")
    hyper_parameters.manually_set_data_and_validate(otx_config_helper.convert(DefaultModelParameters(), target=dict))
    for task_type in [task for task in TaskType if task.is_trainable]:
        model_template_id = task_type.name.lower()
        dataset_requirements = DatasetRequirements()
        if task_type.is_anomaly:
            dataset_requirements.classes = ["Normal", "Anomalous"]
        model_template = ModelTemplate(
            model_template_id=model_template_id,
            model_template_path="",
            name=f"dummy_{model_template_id}",
            task_type=task_type,
            task_family=TaskFamily.VISION,
            instantiation=InstantiationType.NONE,
            hyper_parameters=hyper_parameters,
            dataset_requirements=dataset_requirements,
            capabilities=["compute_representations"],
        )
        model_template_list.register_model_template(model_template)
        request.addfinalizer(lambda: model_template_list.unregister_model_template(model_template_id))
