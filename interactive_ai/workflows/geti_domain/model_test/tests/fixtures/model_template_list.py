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


@pytest.fixture
def fxt_model_template_dataset():
    yield ModelTemplate(
        model_template_id="test_template_dataset",
        model_template_path="",
        name="Sample Dataset Template",
        task_family=TaskFamily.DATASET,
        task_type=TaskType.DATASET,
        is_trainable=False,
        instantiation=InstantiationType.NONE,
        gigaflops=5,
        size=200.5,
        framework="dummy framework",
    )


@pytest.fixture
def fxt_model_template_crop():
    yield ModelTemplate(
        model_template_id="test_template_crop",
        model_template_path="",
        name="Sample Crop Template",
        task_family=TaskFamily.FLOW_CONTROL,
        task_type=TaskType.CROP,
        is_trainable=False,
        instantiation=InstantiationType.NONE,
        framework="dummy framework",
    )


@pytest.fixture
def fxt_model_template_detection():
    hyper_parameters = HyperParameterData(base_path="")
    hyper_parameters.manually_set_data_and_validate(otx_config_helper.convert(DefaultModelParameters(), target=dict))
    model_template = ModelTemplate(
        model_template_id="Mock/Detection",
        model_template_path="",
        name="dummy_detection_task",
        task_type=TaskType.DETECTION,
        task_family=TaskFamily.VISION,
        is_trainable=True,
        instantiation=InstantiationType.NONE,
        hyper_parameters=hyper_parameters,
        capabilities=["compute_representations"],
    )
    ModelTemplateList().register_model_template(model_template=model_template)

    yield model_template

    ModelTemplateList().unregister_model_template(model_template_id=model_template.model_template_id)


@pytest.fixture
def fxt_model_template_classification():
    hyper_parameters = HyperParameterData(base_path="")
    hyper_parameters.manually_set_data_and_validate(otx_config_helper.convert(DefaultModelParameters(), target=dict))
    model_template = ModelTemplate(
        model_template_id="Mock/Classification",
        model_template_path="",
        name="dummy_classification_task",
        task_type=TaskType.CLASSIFICATION,
        task_family=TaskFamily.VISION,
        is_trainable=True,
        instantiation=InstantiationType.NONE,
        hyper_parameters=hyper_parameters,
        capabilities=["compute_representations"],
    )
    ModelTemplateList().register_model_template(model_template=model_template)

    yield model_template

    ModelTemplateList().unregister_model_template(model_template_id=model_template.model_template_id)
