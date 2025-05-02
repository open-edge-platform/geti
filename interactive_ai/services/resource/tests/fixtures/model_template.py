# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pytest
from _pytest.fixtures import FixtureRequest

from iai_core.algorithms import ModelTemplateList
from iai_core.entities.model_template import (
    EntryPoints,
    HyperParameterData,
    InstantiationType,
    ModelTemplate,
    TaskFamily,
    TaskType,
)


@pytest.fixture(autouse=True)
def fxt_register_torch_segmentation_template(request: FixtureRequest):
    """
    This fixture add the model template for the torch_segmentation task to the
    ModelTemplateList.
    """
    model_template_list = ModelTemplateList()
    hyper_parameters = HyperParameterData(base_path="")
    model_template_id = "torch_segmentation"

    torch_segmentation_model_template = ModelTemplate(
        model_template_id=model_template_id,
        model_template_path="",
        name="UNet/DeepLab (PyTorch variant - Class)",
        task_type=TaskType.SEGMENTATION,
        task_family=TaskFamily.VISION,
        instantiation=InstantiationType.CLASS,
        entrypoints=EntryPoints(base="algorithms.torch_segmentation.task.SegmentationTask"),
        hyper_parameters=hyper_parameters,
        is_default_for_task=True,
    )
    model_template_list.register_model_template(torch_segmentation_model_template)
    request.addfinalizer(lambda: model_template_list.unregister_model_template(model_template_id))


@pytest.fixture(autouse=True)
def fxt_register_classification_template(request: FixtureRequest):
    """
    This fixture add the model template for the torch_segmentation task to the
    ModelTemplateList.
    """
    model_template_list = ModelTemplateList()
    hyper_parameters = HyperParameterData(base_path="")
    model_template_id = "classification"

    classification_model_template = ModelTemplate(
        model_template_id=model_template_id,
        model_template_path="",
        name="EfficientNet-B0",
        task_type=TaskType.CLASSIFICATION,
        task_family=TaskFamily.VISION,
        instantiation=InstantiationType.CLASS,
        entrypoints=EntryPoints(base="algorithms.classification.task.ClassificationTask"),
        hyper_parameters=hyper_parameters,
        is_default_for_task=True,
    )
    model_template_list.register_model_template(classification_model_template)
    request.addfinalizer(lambda: model_template_list.unregister_model_template(model_template_id))
