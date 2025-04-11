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
from unittest.mock import MagicMock

import pytest
from sc_sdk.entities.model import (
    Model,
    ModelConfiguration,
    ModelStatus,
    NullModel,
    TrainingFramework,
    TrainingFrameworkType,
)
from sc_sdk.entities.model_storage import ModelStorage, NullModelStorage
from sc_sdk.entities.model_template import (
    DatasetRequirements,
    HyperParameterData,
    InstantiationType,
    ModelTemplate,
    TaskFamily,
    TaskType,
)


@pytest.fixture
def fxt_model_template_anomaly_detection():
    yield ModelTemplate(
        model_template_id="test_template_anomaly_detection",
        model_template_path="",
        name="Sample Anomaly Detection Template",
        task_family=TaskFamily.VISION,
        task_type=TaskType.ANOMALY_DETECTION,
        is_trainable=True,
        hyper_parameters=HyperParameterData(base_path=""),
        instantiation=InstantiationType.NONE,
        gigaflops=24,
        size=88.8,
        framework="dummy framework",
        dataset_requirements=DatasetRequirements(classes=["Normal", "Anomalous"]),
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
    yield ModelStorage(
        id_=fxt_mongo_id(1),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(10),
        model_template=fxt_model_template,
    )


@pytest.fixture
def fxt_model_storage_for_detection_node(fxt_model_template, fxt_mongo_id):
    """It has same task_node_id defined in tests.fixtures.cr_project.fxt_detection_node"""
    yield ModelStorage(
        id_=fxt_mongo_id(1),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(100),
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
    fxt_configurable_parameters_1,
):
    mock_previous_trained_revision = MagicMock(spec=Model)
    mock_previous_trained_revision.configuration = MagicMock()
    mock_previous_trained_revision.configuration.configurable_parameters = fxt_configurable_parameters_1
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        previous_trained_revision=mock_previous_trained_revision,
        data_source_dict={"dummy.file": b"DUMMY_DATA"},
        model_status=ModelStatus.NOT_IMPROVED,
    )


@pytest.fixture
def fxt_obsolete_model(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
    fxt_configurable_parameters_1,
):
    mock_previous_trained_revision = MagicMock(spec=Model)
    mock_previous_trained_revision.configuration = MagicMock()
    mock_previous_trained_revision.configuration.configurable_parameters = fxt_configurable_parameters_1
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        previous_trained_revision=mock_previous_trained_revision,
        data_source_dict={"dummy.file": b"DUMMY_DATA"},
        model_status=ModelStatus.NOT_IMPROVED,
        training_framework=TrainingFramework(type=TrainingFrameworkType.OTX, version="1.6.0"),
    )


@pytest.fixture
def fxt_null_model_storage():
    yield NullModelStorage()


@pytest.fixture
def fxt_model_storage_classification(fxt_empty_project, fxt_model_template_classification, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_empty_project.id_,
        task_node_id=fxt_mongo_id(6),
        model_template=fxt_model_template_classification,
    )


@pytest.fixture
def fxt_model_storage_anomaly_detection(fxt_model_template_anomaly_detection, fxt_mongo_id):
    yield ModelStorage(
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(14),
        model_template=fxt_model_template_anomaly_detection,
        id_=fxt_mongo_id(5),
    )
