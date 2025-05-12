# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from _pytest.fixtures import FixtureRequest
from iai_core.entities.project import Project
from iai_core.entities.task_graph import TaskGraph
from iai_core.repos import ProjectRepo

from tests.fixtures.values import DummyValues, IDOffsets

# @pytest.fixture
# def fxt_project_identifier(fxt_ote_id):
#    yield ProjectIdentifier(
#        workspace_id=fxt_ote_id(1),
#        project_id=fxt_ote_id(2),
#    )


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
    request: FixtureRequest,
    fxt_empty_project,
    fxt_dataset_storage_persisted,
):
    project_repo = ProjectRepo()
    project_repo.save(fxt_empty_project)
    request.addfinalizer(lambda: project_repo.delete_by_id(fxt_empty_project.id_))
    yield fxt_empty_project


# @pytest.fixture
# def fxt_detection_segmentation_chain_project(
#    fxt_dataset_storage,
#    fxt_ote_id,
#    fxt_detection_task,
#    fxt_segmentation_task,
#    fxt_dataset_task,
#    fxt_crop_task,
# ):
#    task_graph = TaskGraph()
#    task_graph.add_node(fxt_dataset_task)
#    task_graph.add_node(fxt_detection_task)
#    task_graph.add_node(fxt_crop_task)
#    task_graph.add_node(fxt_segmentation_task)
#    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_detection_task))
#    task_graph.add_task_edge(TaskEdge(from_task=fxt_detection_task, to_task=fxt_crop_task))
#    task_graph.add_task_edge(TaskEdge(from_task=fxt_crop_task, to_task=fxt_segmentation_task))
#    yield Project(
#        name="dummy_task_chain_project",
#        creator_id="",
#        description="dummy task chain project",
#        dataset_storages=[fxt_dataset_storage],
#        task_graph=task_graph,
#        id=fxt_dataset_storage.project_id,
#        creation_date=DummyValues.CREATION_DATE,
#        user_names=[DummyValues.CREATOR_NAME],
#    )
#
#
# @pytest.fixture
# def fxt_detection_segmentation_chain_project_persisted(
#    request: FixtureRequest,
#    fxt_detection_segmentation_chain_project,
#    fxt_dataset_storage_persisted,
# ):
#    project = fxt_detection_segmentation_chain_project
#    project_repo = ProjectRepo()
#    project_repo.save(project)
#    request.addfinalizer(lambda: project_repo.delete_by_id(project.id_))
#    yield fxt_detection_segmentation_chain_project
#
#
# @pytest.fixture
# def fxt_multi_dataset_storages_project(
#    fxt_ote_id,
#    fxt_dataset_storage,
#    fxt_testing_dataset_storage,
#    fxt_detection_task_graph,
# ):
#    yield Project(
#        name="dummy_multi_dataset_project",
#        creator_id="",
#        description="Sample detection project with multiple dataset storages",
#        user_names=["alice", "bob"],
#        dataset_storages=[fxt_dataset_storage, fxt_testing_dataset_storage],
#        task_graph=fxt_detection_task_graph,
#        id=fxt_ote_id(IDOffsets.SINGLE_TASK_PROJECT),
#    )
#
#
# @pytest.fixture
# def fxt_detection_project(
#    fxt_ote_id,
#    fxt_dataset_storage,
#    fxt_detection_task_graph,
# ):
#    yield Project(
#        name="dummy_multi_dataset_project",
#        creator_id="",
#        description="Sample detection project",
#        user_names=["alice", "bob"],
#        dataset_storages=[fxt_dataset_storage],
#        task_graph=fxt_detection_task_graph,
#        id=fxt_ote_id(IDOffsets.SINGLE_TASK_PROJECT),
#    )
