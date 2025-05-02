# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from copy import copy

import pytest
from iai_core.adapters.model_adapter import ExportableCodeAdapter
from iai_core.configuration.elements.default_model_parameters import DefaultModelParameters
from iai_core.entities.datasets import NullDataset
from iai_core.entities.label_schema import NullLabelSchema
from iai_core.entities.model import (
    Model,
    ModelConfiguration,
    ModelOptimizationType,
    ModelStatus,
    TrainingFramework,
    TrainingFrameworkType,
)
from iai_core.entities.model_storage import ModelStorage
from iai_core.repos import ModelRepo


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
