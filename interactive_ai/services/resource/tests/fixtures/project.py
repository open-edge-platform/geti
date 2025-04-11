# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

import pytest

from geti_types import ProjectIdentifier
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.project import Project
from sc_sdk.repos import ProjectRepo
from sc_sdk.repos.project_repo_helpers import ProjectQueryData, ProjectSortBy, ProjectSortDirection


@pytest.fixture
def fxt_project_identifier(fxt_mongo_id):
    yield ProjectIdentifier(
        workspace_id=fxt_mongo_id(1),
        project_id=fxt_mongo_id(2),
    )


@pytest.fixture
def fxt_empty_project_persisted(fxt_project):
    project_repo = ProjectRepo()
    project_repo.save(fxt_project)
    yield fxt_project


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
def fxt_testing_dataset_storage(fxt_mongo_id):
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
