# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID, ProjectIdentifier
from pytest import FixtureRequest
from sc_sdk.configuration.elements.default_model_parameters import DefaultModelParameters
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.label import Label
from sc_sdk.entities.label_schema import NullLabelSchema
from sc_sdk.entities.model import Model, ModelConfiguration, ModelStatus
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_graph import TaskGraph
from sc_sdk.repos import DatasetRepo, DatasetStorageRepo, LabelRepo, LabelSchemaRepo, ModelRepo, ProjectRepo
from sc_sdk.services.model_service import ModelService
from sc_sdk.utils.deletion_helpers import DeletionHelpers

from tests.test_helpers import (
    TestProject,
    generate_and_save_random_simple_segmentation_project,
    generate_training_dataset_of_all_annotated_media_in_project,
)


@pytest.fixture(scope="function")
def project_empty(request):
    name = "Empty project"
    task_graph = TaskGraph()

    project_id = ProjectRepo.generate_id()
    project_identifier = ProjectIdentifier(workspace_id=ID(""), project_id=project_id)

    ds_repo = DatasetStorageRepo(project_identifier)
    dataset_storage = DatasetStorage(
        name=name,
        project_id=project_id,
        _id=DatasetStorageRepo.generate_id(),
        use_for_training=True,
    )
    ds_repo.save(dataset_storage)
    request.addfinalizer(lambda: ds_repo.delete_by_id(dataset_storage.id_))

    proj_repo = ProjectRepo()
    project = Project(
        name=name,
        creator_id="",
        description="",
        task_graph=task_graph,
        dataset_storages=[dataset_storage],
        id=project_id,
    )
    proj_repo.save(project)
    request.addfinalizer(lambda: proj_repo.delete_by_id(project.id_))

    return project


@pytest.fixture(scope="function")
def project_with_data(request, sample_project: Project):
    dataset = sample_dataset(sample_project)
    labels = list(LabelRepo(sample_project.identifier).get_all())
    request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=sample_project.id_))
    return TestProject(
        project=sample_project,
        dataset=dataset,
        segmentation_model=sample_segmentation_model(sample_project, dataset),
        circle_dataset=circle_dataset(dataset, labels),
        triangle_dataset=triangle_dataset(dataset, labels),
    )


def sample_segmentation_model(project, dataset):
    task_node = project.tasks[-1]
    assert task_node.task_properties.is_trainable
    task_label_schema = LabelSchemaRepo(project.identifier).get_latest_view_by_task(task_node_id=task_node.id_)
    assert not isinstance(task_label_schema, NullLabelSchema)
    configuration = ModelConfiguration(
        configurable_parameters=DefaultModelParameters(),
        label_schema=task_label_schema,
    )
    segmentation_model = Model(
        project=project,
        model_storage=ModelService.get_active_model_storage(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
        ),
        train_dataset=dataset,
        configuration=configuration,
        id_=ModelRepo.generate_id(),
        model_status=ModelStatus.NOT_IMPROVED,
    )
    return segmentation_model


def triangle_dataset(dataset: Dataset, labels: list[Label]):
    triangle_label_id = next(label.id_ for label in labels if labels.name == "triangle")
    return get_figures_dataset(dataset, triangle_label_id)


def circle_dataset(dataset: Dataset, labels: list[Label]):
    circle_label_id = next(label.id_ for label in labels if labels.name == "ellipse")
    return get_figures_dataset(dataset, circle_label_id)


def empty_dataset_item(dataset):
    return [item for item in dataset if len(item.annotation_scene.get_label_ids()) == 0][0]


@pytest.fixture(scope="function")
def sample_project(request: FixtureRequest) -> Project:
    return generate_and_save_random_simple_segmentation_project(request, projectname="__Test_evaluation_project")


def sample_dataset(project):
    return generate_training_dataset_of_all_annotated_media_in_project(project)[1]


def get_figures_dataset(dataset: Dataset, figure_label_id: ID):
    items = [
        item
        for item in dataset
        if len(item.annotation_scene.get_label_ids()) > 0 and figure_label_id in item.annotation_scene.get_label_ids()
    ][:3]
    return Dataset(items=items, id=DatasetRepo.generate_id())


@pytest.fixture
def fxt_mongo_id():
    """
    Create a realistic MongoDB ID string for testing purposes.

    If you need multiple ones, call this fixture repeatedly with different arguments.
    """
    base_id: int = 0x60D31793D5F1FB7E6E3C1A4F

    def _build_id(offset: int = 0) -> str:
        return str(hex(base_id + offset))[2:]

    yield _build_id


@pytest.fixture
def fxt_ote_id(fxt_mongo_id):
    """
    Create a realistic OTE ID for testing purposes. Based on the fxt_mongo_id, but this
    fixture returns an actual ID entity instead of a string.
    """

    def _build_ote_id(offset: int = 0) -> ID:
        return ID(fxt_mongo_id(offset))

    yield _build_ote_id
