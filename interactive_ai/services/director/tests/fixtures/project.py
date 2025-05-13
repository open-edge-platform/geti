# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from tests.fixtures.values import DummyValues, IDOffsets

from geti_types import ProjectIdentifier
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.project import Project
from iai_core.entities.task_graph import TaskGraph
from iai_core.repos import ProjectRepo
from iai_core.repos.project_repo_helpers import ProjectQueryData, ProjectSortBy, ProjectSortDirection


@pytest.fixture
def fxt_project_identifier(fxt_ote_id):
    yield ProjectIdentifier(
        workspace_id=fxt_ote_id(1),
        project_id=fxt_ote_id(2),
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
def fxt_empty_project_persisted(
    fxt_empty_project,
):
    project_repo = ProjectRepo()
    project_repo.save(fxt_empty_project)
    yield fxt_empty_project


@pytest.fixture
def fxt_dataset_storage(fxt_mongo_id):
    dataset_storage = DatasetStorage(
        name="dummy_dataset_storage",
        project_id=fxt_mongo_id(2),
        _id=fxt_mongo_id(3),
        use_for_training=True,
    )
    yield dataset_storage


@pytest.fixture
def fxt_testing_dataset_storage(fxt_mongo_id, fxt_workspace_id):
    yield DatasetStorage(
        name="dummy_test_dataset_storage",
        project_id=fxt_mongo_id(2),
        use_for_training=False,
        _id=fxt_mongo_id(1),
    )


@pytest.fixture
def fxt_dataset_storage_identifier(fxt_dataset_storage):
    return fxt_dataset_storage.identifier


@pytest.fixture
def fxt_project_with_classification_task(fxt_mongo_id, fxt_dataset_storage, fxt_classification_task_graph):
    yield Project(
        name="dummy_classification_project",
        description="Sample project with a classification task",
        creator_id="",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_classification_task_graph,
        id=fxt_mongo_id(2),
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
        id=fxt_mongo_id(2),
    )
    yield project


@pytest.fixture
def fxt_multi_dataset_storages_project(
    fxt_mongo_id,
    fxt_dataset_storage,
    fxt_testing_dataset_storage,
    fxt_detection_task_graph,
):
    yield Project(
        name="dummy_multi_dataset_project",
        creator_id="",
        description="Sample detection project with multiple dataset storages",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage, fxt_testing_dataset_storage],
        task_graph=fxt_detection_task_graph,
        id=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_project_with_segmentation_task(fxt_mongo_id, fxt_dataset_storage, fxt_segmentation_task_graph):
    yield Project(
        name="dummy_segmentation_project",
        creator_id="",
        description="Sample project with a segmentation task",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_segmentation_task_graph,
        id=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_project_with_keypoint_detection_task(fxt_mongo_id, fxt_dataset_storage, fxt_keypoint_detection_task_graph):
    yield Project(
        name="dummy_keypoint_detection_project",
        creator_id="",
        description="Sample project with a keypoint detection task",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_keypoint_detection_task_graph,
        id=fxt_mongo_id(2),
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
        id=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_project_with_anomaly_detection_task(fxt_mongo_id, fxt_dataset_storage, fxt_anomaly_detection_task_graph):
    yield Project(
        name="dummy_anomaly_detection_project",
        creator_id="",
        description="Sample project with an anomaly detection task",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_anomaly_detection_task_graph,
        id=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_project(fxt_project_with_detection_task):
    yield fxt_project_with_detection_task


@pytest.fixture
def fxt_project_rest(fxt_project, fxt_organization_id, fxt_task_graph_rest):
    yield {
        "datasets": [],
        "id": fxt_project.id_,
        "creator_id": fxt_project.creator_id,
        "name": fxt_project.name,
        "pipeline": fxt_task_graph_rest,
        "creation_time": fxt_project.creation_date.isoformat(),
        "thumbnail": f"/api/v1/organizations/{fxt_organization_id}/workspaces/{fxt_project.workspace_id}"
        f"/projects/{fxt_project.id_}/thumbnail",
    }


@pytest.fixture
def fxt_detection_segmentation_chain_project(
    fxt_mongo_id,
    fxt_dataset_storage,
    fxt_detection_segmentation_task_graph,
):
    yield Project(
        name="dummy_detection_segmentation_chain_project",
        creator_id="",
        description="Sample detection->segmentation project",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_detection_segmentation_task_graph,
        id=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_detection_classification_chain_project(
    fxt_mongo_id,
    fxt_dataset_storage,
    fxt_detection_classification_task_graph,
):
    yield Project(
        name="dummy_detection_classification_chain_project",
        creator_id="",
        description="Sample detection->classification project",
        user_names=["alice", "bob"],
        dataset_storages=[fxt_dataset_storage],
        task_graph=fxt_detection_classification_task_graph,
        id=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_chain_project(fxt_detection_segmentation_chain_project):
    yield fxt_detection_segmentation_chain_project


@pytest.fixture
def fxt_project_query_data():
    yield ProjectQueryData(
        skip=0,
        limit=10,
        name="",
        sort_by=ProjectSortBy.CREATION_DATE,
        sort_direction=ProjectSortDirection.DSC,
        with_size=False,
    )
