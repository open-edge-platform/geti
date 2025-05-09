# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from iai_core.algorithms import ModelTemplateList
from iai_core.entities.color import Color
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelSchemaView
from iai_core.entities.model_template import TaskType
from iai_core.entities.task_graph import TaskEdge, TaskGraph
from iai_core.entities.task_node import TaskNode, TaskProperties

from .values import DummyValues, IDOffsets
from geti_types import ID


@pytest.fixture
def fxt_dataset_task_factory(fxt_ote_id, fxt_model_template_dataset, fxt_label_schema):
    def _dataset_task_factory(project_id: ID):
        return TaskNode(
            title="dummy dataset task",
            task_properties=TaskProperties.from_model_template(fxt_model_template_dataset),
            project_id=project_id,
            id_=fxt_ote_id(IDOffsets.DATASET_TASK),
        )

    yield _dataset_task_factory


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
def fxt_segmentation_task(fxt_ote_id, fxt_empty_project):
    yield TaskNode(
        title="dummy segmentation task",
        task_properties=TaskProperties.from_model_template(ModelTemplateList().get_by_id("segmentation")),
        project_id=fxt_ote_id(IDOffsets.TASK_CHAIN_PROJECT),
        id_=fxt_ote_id(IDOffsets.SEGMENTATION_TASK),
    )


@pytest.fixture
def fxt_label(fxt_ote_id):
    yield Label(
        name=DummyValues.LABEL_NAME,
        domain=Domain.DETECTION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        id_=fxt_ote_id(IDOffsets.DETECTION_LABELS),
    )


@pytest.fixture
def fxt_label_schema(fxt_label):
    yield LabelSchemaView.from_labels([fxt_label])


@pytest.fixture
def fxt_label_2(fxt_ote_id):
    yield Label(
        name=DummyValues.LABEL_NAME,
        domain=Domain.DETECTION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        id_=fxt_ote_id(IDOffsets.TASK_CHAIN_PROJECT),
    )


@pytest.fixture
def fxt_label_3(fxt_ote_id):
    yield Label(
        name=DummyValues.LABEL_NAME,
        domain=Domain.KEYPOINT_DETECTION,
        color=Color.from_hex_str("#ff0000"),
        hotkey=DummyValues.LABEL_HOTKEY,
        id_=fxt_ote_id(10),
    )


@pytest.fixture
def fxt_label_schema_2(fxt_label_2):
    yield LabelSchemaView.from_labels([fxt_label_2])


@pytest.fixture
def fxt_dataset_task(fxt_ote_id, fxt_model_template_dataset):
    yield TaskNode(
        title="Sample dataset task",
        task_properties=TaskProperties.from_model_template(fxt_model_template_dataset),
        project_id=ID(fxt_ote_id(IDOffsets.TASK_CHAIN_PROJECT)),
        id_=ID(fxt_ote_id(IDOffsets.DATASET_TASK)),
    )


@pytest.fixture
def fxt_crop_task(fxt_ote_id, fxt_model_template_crop, fxt_label_schema):
    yield TaskNode(
        title="Sample crop task",
        task_properties=TaskProperties.from_model_template(fxt_model_template_crop),
        project_id=ID(fxt_ote_id(IDOffsets.TASK_CHAIN_PROJECT)),
        id_=ID(fxt_ote_id(IDOffsets.CROP_TASK)),
    )


@pytest.fixture
def fxt_task_factory(fxt_ote_id, fxt_label_schema_factory):
    def _task_factory(project_id: ID, task_type: TaskType = TaskType.CLASSIFICATION):
        task_name = task_type.name.lower()
        id_offset = getattr(IDOffsets, f"{task_name.upper()}_TASK")
        return TaskNode(
            title=f"dummy {task_name} task",
            task_properties=TaskProperties.from_model_template(ModelTemplateList().get_by_id(task_name)),
            project_id=project_id,
            id_=fxt_ote_id(id_offset),
        )

    yield _task_factory


@pytest.fixture
def fxt_detection_task_graph(fxt_ote_id, fxt_classification_task, fxt_detection_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_classification_task)
    task_graph.add_node(fxt_detection_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_classification_task, to_task=fxt_detection_task))
    yield task_graph
