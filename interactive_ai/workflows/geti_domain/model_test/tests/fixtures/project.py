# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from iai_core.entities.project import Project
from iai_core.entities.task_graph import TaskGraph

from tests.fixtures.values import DummyValues, IDOffsets


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
    yield Project(
        name="dummy_detection_project",
        description="Sample project with a detection task",
        creator_id="",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_detection_task_graph,
        id=fxt_mongo_id(1),
    )


@pytest.fixture
def fxt_project(fxt_project_with_detection_task):
    yield fxt_project_with_detection_task


@pytest.fixture
def fxt_project_with_classification_task(fxt_mongo_id, fxt_dataset_storage, fxt_classification_task_graph):
    yield Project(
        name="dummy_classification_project",
        description="Sample project with a classification task",
        creator_id="",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_classification_task_graph,
        id=fxt_mongo_id(1),
    )


@pytest.fixture
def fxt_project_with_anomaly_classification_task(
    fxt_mongo_id,
    fxt_dataset_storage,
    fxt_anomaly_classification_task_graph,
):
    yield Project(
        name="dummy_anomaly_classification_project",
        creator_id="",
        description="Sample project with an anomaly classification task",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_anomaly_classification_task_graph,
        id=fxt_mongo_id(1),
    )
