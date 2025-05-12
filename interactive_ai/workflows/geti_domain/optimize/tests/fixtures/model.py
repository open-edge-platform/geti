# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
from iai_core.entities.model_storage import ModelStorage, ModelStorageIdentifier
from iai_core.repos import ModelRepo


def empty_model_configuration() -> ModelConfiguration:
    return ModelConfiguration(DefaultModelParameters(), NullLabelSchema())


@pytest.fixture
def fxt_training_framework():
    yield TrainingFramework(type=TrainingFrameworkType.OTX, version="1.6.0")


@pytest.fixture
def fxt_model_storage_identifier(fxt_ote_id):
    yield ModelStorageIdentifier(
        workspace_id=fxt_ote_id(1),
        project_id=fxt_ote_id(2),
        model_storage_id=fxt_ote_id(3),
    )


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
def fxt_model_storage(fxt_model_storage_detection):
    yield fxt_model_storage_detection


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
