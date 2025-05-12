# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest
from iai_core.algorithms import ModelTemplateList
from iai_core.entities.project import Project
from iai_core.entities.task_graph import TaskEdge, TaskGraph
from iai_core.entities.task_node import TaskNode, TaskProperties

from tests.fixtures.values import DummyValues, IDOffsets


@pytest.fixture
def fxt_classification_task(fxt_ote_id, fxt_model_storage_classification):
    yield TaskNode(
        title="dummy classification task",
        task_properties=TaskProperties.from_model_template(ModelTemplateList().get_by_id("classification")),
        project_id=fxt_ote_id(IDOffsets.TASK_CHAIN_PROJECT),
        id_=fxt_ote_id(IDOffsets.CLASSIFICATION_TASK),
    )


@pytest.fixture
def fxt_empty_project(fxt_dataset_storage, fxt_ote_id):
    yield Project(
        name="dummy_empty_project",
        creator_id="",
        description="dummy empty project",
        dataset_storages=[fxt_dataset_storage],
        task_graph=TaskGraph(),
        id=fxt_ote_id(IDOffsets.EMPTY_PROJECT),
        creation_date=DummyValues.CREATION_DATE,
        user_names=[DummyValues.CREATOR_NAME],
    )


@pytest.fixture
def fxt_project_with_detection_task(fxt_mongo_id, fxt_dataset_storage, fxt_detection_task_graph):
    project = Project(
        name="dummy_detection_project",
        description="Sample project with a detection task",
        creator_id="",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_detection_task_graph,
        id=fxt_mongo_id(1),
    )
    with patch.object(project, "get_training_dataset_storage", return_value=fxt_dataset_storage):
        yield project


@pytest.fixture
def fxt_project(fxt_project_with_detection_task):
    yield fxt_project_with_detection_task


@pytest.fixture
def fxt_detection_task_graph(fxt_ote_id, fxt_classification_task, fxt_detection_task):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_classification_task)
    task_graph.add_node(fxt_detection_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_classification_task, to_task=fxt_detection_task))
    yield task_graph


@pytest.fixture
def fxt_detection_project(
    fxt_ote_id,
    fxt_dataset_storage,
    fxt_detection_task_graph,
):
    yield Project(
        name="dummy_multi_dataset_project",
        creator_id="",
        description="Sample detection project",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_detection_task_graph,
        id=fxt_ote_id(IDOffsets.SINGLE_TASK_PROJECT),
    )
