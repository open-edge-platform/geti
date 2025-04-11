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
import pytest
from _pytest.fixtures import FixtureRequest

from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.model_template import (
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
