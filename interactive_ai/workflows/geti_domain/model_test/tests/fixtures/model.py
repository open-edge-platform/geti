# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from copy import copy

import pytest
from iai_core_py.entities.model import Model, ModelConfiguration, ModelStatus, NullModel
from iai_core_py.entities.model_storage import ModelStorage, NullModelStorage
from iai_core_py.entities.model_template import (
    DatasetRequirements,
    HyperParameterData,
    InstantiationType,
    ModelTemplate,
    TaskFamily,
    TaskType,
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
def fxt_model_storage_detection_2(fxt_model_template_detection, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(6),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(12),
        model_template=fxt_model_template_detection,
    )


@pytest.fixture
def fxt_model_template_anomaly_classification():
    yield ModelTemplate(
        model_template_id="test_template_anomaly_classification",
        model_template_path="",
        name="Sample Anomaly Classification Template",
        task_family=TaskFamily.VISION,
        task_type=TaskType.ANOMALY_CLASSIFICATION,
        is_trainable=True,
        hyper_parameters=HyperParameterData(base_path=""),
        instantiation=InstantiationType.NONE,
        gigaflops=24,
        size=88.8,
        framework="dummy framework",
        dataset_requirements=DatasetRequirements(classes=["Normal", "Anomalous"]),
    )


@pytest.fixture
def fxt_model_storage_anomaly_classification(fxt_model_template_anomaly_classification, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(14),
        model_template=fxt_model_template_anomaly_classification,
    )


@pytest.fixture
def fxt_model_storage(fxt_model_template, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(1),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(10),
        model_template=fxt_model_template,
    )


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


@pytest.fixture
def fxt_null_model():
    yield NullModel()


@pytest.fixture
def fxt_model(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        data_source_dict={"dummy.file": b"DUMMY_DATA"},
        model_status=ModelStatus.NOT_IMPROVED,
    )


@pytest.fixture
def fxt_null_model_storage():
    yield NullModelStorage()
