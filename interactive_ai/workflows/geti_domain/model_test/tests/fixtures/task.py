# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest
from geti_types import ID
from iai_core_py.algorithms import ModelTemplateList
from iai_core_py.entities.label_schema import LabelSchemaView
from iai_core_py.entities.model_template import TaskFamily, TaskType
from iai_core_py.entities.task_graph import TaskEdge, TaskGraph
from iai_core_py.entities.task_node import TaskNode, TaskProperties

from tests.fixtures.values import IDOffsets


@pytest.fixture
def fxt_trainable_task(fxt_detection_task):
    yield fxt_detection_task


@pytest.fixture
def fxt_classification_task(fxt_ote_id, fxt_model_storage_classification):
    yield TaskNode(
        title="dummy classification task",
        task_properties=TaskProperties.from_model_template(ModelTemplateList().get_by_id("classification")),
        project_id=fxt_ote_id(IDOffsets.TASK_CHAIN_PROJECT),
        id_=fxt_ote_id(IDOffsets.CLASSIFICATION_TASK),
    )


@pytest.fixture
def fxt_detection_task(fxt_ote_id, fxt_empty_project):
    yield TaskNode(
        title="dummy detection task",
        task_properties=TaskProperties.from_model_template(ModelTemplateList().get_by_id("detection")),
        project_id=fxt_ote_id(IDOffsets.TASK_CHAIN_PROJECT),
        id_=fxt_ote_id(IDOffsets.DETECTION_TASK),
    )


@pytest.fixture
def fxt_classification_task_graph(fxt_dataset_task, fxt_classification_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_dataset_task)
    task_graph.add_node(fxt_classification_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_classification_task))
    yield task_graph


@pytest.fixture
def fxt_anomaly_classification_task_graph(fxt_dataset_task, fxt_anomaly_classification_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_dataset_task)
    task_graph.add_node(fxt_anomaly_classification_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_anomaly_classification_task))
    yield task_graph


@pytest.fixture
def fxt_anomaly_classification_task(
    fxt_mongo_id,
    fxt_model_storage_anomaly_classification,
):
    yield TaskNode(
        title="Sample anomaly classification task",
        project_id=fxt_mongo_id(1),
        task_properties=TaskProperties.from_model_template(fxt_model_storage_anomaly_classification.model_template),
        id_=fxt_mongo_id(13),
    )


@pytest.fixture
def fxt_task_node():
    return TaskNode(
        title="Test node",
        project_id=ID("project_id"),
        id_=ID("task_id"),
        task_properties=TaskProperties(
            task_type=TaskType.ANOMALY_DETECTION,
            task_family=TaskFamily.VISION,
            is_trainable=True,
            is_global=False,
            is_anomaly=True,
        ),
    )


@pytest.fixture
def fxt_detection_task_graph(fxt_ote_id, fxt_classification_task, fxt_detection_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_classification_task)
    task_graph.add_node(fxt_detection_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_classification_task, to_task=fxt_detection_task))
    yield task_graph


@pytest.fixture
def fxt_dataset_task(fxt_ote_id, fxt_model_template_dataset):
    yield TaskNode(
        title="Sample dataset task",
        task_properties=TaskProperties.from_model_template(fxt_model_template_dataset),
        project_id=ID(fxt_ote_id(IDOffsets.TASK_CHAIN_PROJECT)),
        id_=ID(fxt_ote_id(IDOffsets.DATASET_TASK)),
    )


@pytest.fixture
def fxt_label_schema(fxt_label):
    yield LabelSchemaView.from_labels([fxt_label])


@pytest.fixture(autouse=True)
def fxt_requests_post():
    """Patch istio-proxy termination callback not to raise an error in local environment."""
    with patch("jobs_common.tasks.primary_container_task.requests.post") as mock_requests_post:
        mock_requests_post.return_value.status_code = 200
        yield mock_requests_post
