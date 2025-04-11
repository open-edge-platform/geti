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

from copy import copy

import pytest
from sc_sdk.adapters.model_adapter import ExportableCodeAdapter
from sc_sdk.configuration.elements.default_model_parameters import DefaultModelParameters
from sc_sdk.entities.datasets import NullDataset
from sc_sdk.entities.label_schema import NullLabelSchema
from sc_sdk.entities.model import (
    Model,
    ModelConfiguration,
    ModelOptimizationType,
    ModelStatus,
    TrainingFramework,
    TrainingFrameworkType,
)
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.repos import ModelRepo


@pytest.fixture
def fxt_training_framework():
    yield TrainingFramework(type=TrainingFrameworkType.OTX, version="1.6.0")


@pytest.fixture
def fxt_model_storage_classification(fxt_empty_project, fxt_model_template_classification, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_empty_project.id_,
        task_node_id=fxt_mongo_id(6),
        model_template=fxt_model_template_classification,
    )


@pytest.fixture
def fxt_model_storage_detection(fxt_empty_project, fxt_model_template_detection, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_empty_project.id_,
        task_node_id=fxt_mongo_id(6),
        model_template=fxt_model_template_detection,
    )


@pytest.fixture
def fxt_model_storage_detection_2(fxt_model_template_detection, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(6),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(12),
        model_template=fxt_model_template_detection,
    )


@pytest.fixture
def fxt_model_storage(fxt_model_template, fxt_mongo_id):
    model_storage = ModelStorage(
        id_=fxt_mongo_id(1),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(10),
        model_template=fxt_model_template,
    )
    yield model_storage


@pytest.fixture
def fxt_model_template_1(fxt_model_template_dataset):
    yield fxt_model_template_dataset


@pytest.fixture
def fxt_model_template(fxt_model_template_1):
    yield fxt_model_template_1


@pytest.fixture
def fxt_model_not_ready(fxt_model):
    model = copy(fxt_model)
    model.model_status = ModelStatus.NOT_READY
    yield model


@pytest.fixture
def fxt_model_trained_no_stats(fxt_model):
    model = copy(fxt_model)
    model.model_status = ModelStatus.TRAINED_NO_STATS
    yield model


def empty_model_configuration() -> ModelConfiguration:
    return ModelConfiguration(DefaultModelParameters(), NullLabelSchema())


@pytest.fixture
def fxt_model_success(fxt_empty_project, fxt_model_storage_detection, fxt_training_framework):
    yield Model(
        project=fxt_empty_project,
        model_storage=fxt_model_storage_detection,
        train_dataset=NullDataset(),
        configuration=empty_model_configuration(),
        id_=ModelRepo.generate_id(),
        data_source_dict={"inference_model.bin": b"weights_data"},
        training_framework=fxt_training_framework,
        model_status=ModelStatus.SUCCESS,
        exportable_code_adapter=ExportableCodeAdapter(data_source=b"exportable_code"),
    )


@pytest.fixture
def fxt_model_failed(fxt_empty_project, fxt_model_storage_detection, fxt_training_framework):
    yield Model(
        project=fxt_empty_project,
        model_storage=fxt_model_storage_detection,
        train_dataset=NullDataset(),
        configuration=empty_model_configuration(),
        id_=ModelRepo.generate_id(),
        training_framework=fxt_training_framework,
        model_status=ModelStatus.FAILED,
    )


@pytest.fixture
def fxt_model_optimized(fxt_empty_project, fxt_model_storage_detection, fxt_training_framework):
    yield Model(
        project=fxt_empty_project,
        model_storage=fxt_model_storage_detection,
        train_dataset=NullDataset(),
        configuration=empty_model_configuration(),
        id_=ModelRepo.generate_id(),
        data_source_dict={"inference_model.bin": b"optimized_weights_data"},
        training_framework=fxt_training_framework,
        model_status=ModelStatus.SUCCESS,
        optimization_type=ModelOptimizationType.POT,
        exportable_code_adapter=ExportableCodeAdapter(data_source=b"exportable_code"),
    )


@pytest.fixture
def fxt_model(fxt_model_success):
    yield fxt_model_success
