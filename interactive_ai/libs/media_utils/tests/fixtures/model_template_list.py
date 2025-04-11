# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
import sc_sdk.configuration.helper as otx_config_helper
from _pytest.fixtures import FixtureRequest
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.configuration.elements.default_model_parameters import DefaultModelParameters
from sc_sdk.entities.model_template import (
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
