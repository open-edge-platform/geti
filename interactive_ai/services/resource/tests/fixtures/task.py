# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from geti_types import ID
from sc_sdk.entities.keypoint_structure import KeypointEdge, KeypointPosition, KeypointStructure
from sc_sdk.entities.task_graph import TaskEdge, TaskGraph
from sc_sdk.entities.task_node import TaskNode, TaskProperties


@pytest.fixture
def fxt_dataset_task(fxt_mongo_id, fxt_model_template_dataset):
    yield TaskNode(
        title="Sample dataset task",
        task_properties=TaskProperties.from_model_template(fxt_model_template_dataset),
        project_id=ID(fxt_mongo_id(1)),
        id_=ID(fxt_mongo_id(10)),
    )


@pytest.fixture
def fxt_dataset_task_rest(fxt_dataset_task):
    yield {
        "id": fxt_dataset_task.id_,
        "title": fxt_dataset_task.title,
        "task_type": fxt_dataset_task.task_properties.task_type.name.lower(),
    }


@pytest.fixture
def fxt_classification_task(fxt_mongo_id, fxt_model_template_classification):
    yield TaskNode(
        title="Sample classification task",
        project_id=fxt_mongo_id(1),
        task_properties=TaskProperties.from_model_template(fxt_model_template_classification),
        id_=fxt_mongo_id(11),
    )


@pytest.fixture
def fxt_classification_task_rest(fxt_classification_task):
    yield {
        "id": fxt_classification_task.id_,
        "title": fxt_classification_task.title,
        "task_type": fxt_classification_task.task_properties.task_type.name.lower(),
    }


@pytest.fixture
def fxt_detection_task(fxt_mongo_id, fxt_model_template_detection):
    yield TaskNode(
        title="Sample detection task",
        project_id=fxt_mongo_id(1),
        task_properties=TaskProperties.from_model_template(fxt_model_template_detection),
        id_=fxt_mongo_id(12),
    )


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
def fxt_anomaly_detection_task(
    fxt_mongo_id,
    fxt_model_storage_anomaly_detection,
):
    yield TaskNode(
        title="Sample anomaly detection task",
        project_id=fxt_mongo_id(1),
        task_properties=TaskProperties.from_model_template(fxt_model_storage_anomaly_detection.model_template),
        id_=fxt_mongo_id(13),
    )


@pytest.fixture
def fxt_detection_task_rest(fxt_detection_task):
    yield {
        "id": fxt_detection_task.id_,
        "title": fxt_detection_task.title,
        "task_type": fxt_detection_task.task_properties.task_type.name.lower(),
    }


@pytest.fixture
def fxt_segmentation_task(
    fxt_mongo_id,
    fxt_model_storage_segmentation,
):
    yield TaskNode(
        title="Sample segmentation task",
        project_id=fxt_mongo_id(1),
        task_properties=TaskProperties.from_model_template(fxt_model_storage_segmentation.model_template),
        id_=fxt_mongo_id(14),
    )


@pytest.fixture
def fxt_crop_task(fxt_mongo_id, fxt_model_template_crop, fxt_label_schema):
    yield TaskNode(
        title="Sample crop task",
        task_properties=TaskProperties.from_model_template(fxt_model_template_crop),
        project_id=ID(fxt_mongo_id(1)),
        id_=ID(fxt_mongo_id(15)),
    )


@pytest.fixture
def fxt_crop_task_rest(fxt_crop_task):
    yield {
        "id": fxt_crop_task.id_,
        "title": fxt_crop_task.title,
        "task_type": fxt_crop_task.task_properties.task_type.name.lower(),
    }


@pytest.fixture
def fxt_keypoint_task(fxt_mongo_id, fxt_model_template_keypoint_detection, fxt_label_schema):
    yield TaskNode(
        title="Sample keypoint detection task",
        task_properties=TaskProperties.from_model_template(fxt_model_template_keypoint_detection),
        project_id=ID(fxt_mongo_id(1)),
        id_=ID(fxt_mongo_id(15)),
    )


@pytest.fixture
def fxt_keypoint_detection_task_rest(fxt_keypoint_task):
    yield {
        "id": fxt_keypoint_task.id_,
        "title": fxt_keypoint_task.title,
        "task_type": fxt_keypoint_task.task_properties.task_type.name.lower(),
    }


@pytest.fixture
def fxt_task_1(fxt_dataset_task):
    yield fxt_dataset_task


@pytest.fixture
def fxt_task_1_rest(fxt_dataset_task_rest):
    yield fxt_dataset_task_rest


@pytest.fixture
def fxt_task_2(fxt_detection_task):
    yield fxt_detection_task


@pytest.fixture
def fxt_task_2_rest(fxt_detection_task_rest):
    yield fxt_detection_task_rest


@pytest.fixture
def fxt_task(fxt_task_1):
    yield fxt_task_1


@pytest.fixture
def fxt_trainable_task(fxt_detection_task):
    yield fxt_detection_task


@pytest.fixture
def fxt_task_edge(fxt_task_1, fxt_task_2):
    yield TaskEdge(
        from_task=fxt_task_1,
        to_task=fxt_task_2,
    )


@pytest.fixture
def fxt_task_edge_rest(fxt_task_1, fxt_task_2):
    yield {
        "from": str(fxt_task_1.id_),
        "to": str(fxt_task_2.id_),
    }


@pytest.fixture
def fxt_classification_task_graph(fxt_dataset_task, fxt_classification_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_dataset_task)
    task_graph.add_node(fxt_classification_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_classification_task))
    yield task_graph


@pytest.fixture
def fxt_detection_task_graph(fxt_dataset_task, fxt_detection_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_dataset_task)
    task_graph.add_node(fxt_detection_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_detection_task))
    yield task_graph


@pytest.fixture
def fxt_segmentation_task_graph(fxt_dataset_task, fxt_segmentation_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_dataset_task)
    task_graph.add_node(fxt_segmentation_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_segmentation_task))
    yield task_graph


@pytest.fixture
def fxt_anomaly_classification_task_graph(fxt_dataset_task, fxt_anomaly_classification_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_dataset_task)
    task_graph.add_node(fxt_anomaly_classification_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_anomaly_classification_task))
    yield task_graph


@pytest.fixture
def fxt_anomaly_detection_task_graph(fxt_dataset_task, fxt_anomaly_detection_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_dataset_task)
    task_graph.add_node(fxt_anomaly_detection_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_anomaly_detection_task))
    yield task_graph


@pytest.fixture
def fxt_detection_segmentation_task_graph(
    fxt_dataset_task,
    fxt_detection_task,
    fxt_segmentation_task,
    fxt_crop_task,
):
    task_nodes = (
        fxt_dataset_task,
        fxt_detection_task,
        fxt_crop_task,
        fxt_segmentation_task,
    )
    task_graph = TaskGraph()
    for node in task_nodes:
        task_graph.add_node(node)
    for i in range(len(task_nodes) - 1):
        task_graph.add_task_edge(TaskEdge(from_task=task_nodes[i], to_task=task_nodes[i + 1]))
    yield task_graph


@pytest.fixture
def fxt_detection_classification_task_graph(
    fxt_dataset_task,
    fxt_classification_task,
    fxt_detection_task,
    fxt_crop_task,
):
    task_nodes = (
        fxt_dataset_task,
        fxt_detection_task,
        fxt_crop_task,
        fxt_classification_task,
    )
    task_graph = TaskGraph()
    for node in task_nodes:
        task_graph.add_node(node)
    for i in range(len(task_nodes) - 1):
        task_graph.add_task_edge(TaskEdge(from_task=task_nodes[i], to_task=task_nodes[i + 1]))
    yield task_graph


@pytest.fixture
def fxt_task_graph(fxt_detection_task_graph):
    yield fxt_detection_task_graph


@pytest.fixture
def fxt_task_graph_rest(fxt_task_1_rest, fxt_task_2_rest, fxt_task_edge_rest):
    yield {
        "tasks": [fxt_task_1_rest, fxt_task_2_rest],
        "connections": [fxt_task_edge_rest],
    }


@pytest.fixture
def fxt_keypoint_structure(fxt_task_1_rest, fxt_task_2_rest, fxt_task_edge_rest):
    yield KeypointStructure(
        edges=[KeypointEdge(node_1=ID("node_1"), node_2=ID("node_2"))],
        positions=[KeypointPosition(node=ID("node_1"), x=0, y=0), KeypointPosition(node=ID("node_2"), x=1, y=1)],
    )


@pytest.fixture
def fxt_keypoint_structure_rest(fxt_task_1_rest, fxt_task_2_rest, fxt_task_edge_rest):
    yield {
        "edges": [{"nodes": ["node_1", "node_2"]}],
        "positions": [{"label": "node_1", "x": 0, "y": 0}, {"label": "node_2", "x": 1, "y": 1}],
    }
