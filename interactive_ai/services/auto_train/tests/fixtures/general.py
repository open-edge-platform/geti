# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pytest

import sc_sdk.configuration.helper as otx_config_helper
from geti_types import ID, make_session, session_context
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.configuration.elements.default_model_parameters import DefaultModelParameters
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.entities.model_template import HyperParameterData, InstantiationType, ModelTemplate, TaskFamily, TaskType
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_graph import TaskGraph
from sc_sdk.entities.task_node import TaskNode, TaskProperties


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


@pytest.fixture
def fxt_dataset_storage(fxt_ote_id):
    dataset_storage = DatasetStorage(
        name="dummy_dataset_storage",
        project_id=fxt_ote_id(),
        _id=fxt_ote_id(),
        use_for_training=True,
    )
    yield dataset_storage


@pytest.fixture
def fxt_empty_project(fxt_dataset_storage, fxt_ote_id):
    yield Project(
        name="dummy_empty_project",
        creator_id="",
        description="dummy empty project",
        dataset_storages=[fxt_dataset_storage],
        task_graph=TaskGraph(),
        id=fxt_ote_id(),
    )


@pytest.fixture(scope="session", autouse=True)
def fxt_session():
    """Initialize the session context variable with a default Session object"""
    session = make_session()
    with session_context(session=session):
        yield session


@pytest.fixture
def fxt_model_template_dataset():
    yield ModelTemplate(
        model_template_id="test_template_dataset",
        model_template_path="",
        name="Sample Dataset Template",
        task_family=TaskFamily.DATASET,
        task_type=TaskType.DATASET,
        is_trainable=False,
        instantiation=InstantiationType.NONE,
        gigaflops=5,
        size=200.5,
        framework="dummy framework",
    )


@pytest.fixture
def fxt_model_storage_classification(fxt_empty_project, fxt_model_template_classification, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_empty_project.id_,
        task_node_id=fxt_mongo_id(6),
        model_template=fxt_model_template_classification,
    )


@pytest.fixture
def fxt_model_template_classification():
    hyper_parameters = HyperParameterData(base_path="")
    hyper_parameters.manually_set_data_and_validate(otx_config_helper.convert(DefaultModelParameters(), target=dict))
    model_template = ModelTemplate(
        model_template_id="Mock/Classification",
        model_template_path="",
        name="dummy_classification_task",
        task_type=TaskType.CLASSIFICATION,
        task_family=TaskFamily.VISION,
        is_trainable=True,
        instantiation=InstantiationType.NONE,
        hyper_parameters=hyper_parameters,
        capabilities=["compute_representations"],
    )
    ModelTemplateList().register_model_template(model_template=model_template)

    yield model_template

    ModelTemplateList().unregister_model_template(model_template_id=model_template.model_template_id)


@pytest.fixture
def fxt_model_template_detection():
    hyper_parameters = HyperParameterData(base_path="")
    hyper_parameters.manually_set_data_and_validate(otx_config_helper.convert(DefaultModelParameters(), target=dict))
    model_template = ModelTemplate(
        model_template_id="Mock/Detection",
        model_template_path="",
        name="dummy_detection_task",
        task_type=TaskType.DETECTION,
        task_family=TaskFamily.VISION,
        is_trainable=True,
        instantiation=InstantiationType.NONE,
        hyper_parameters=hyper_parameters,
        capabilities=["compute_representations"],
    )
    ModelTemplateList().register_model_template(model_template=model_template)

    yield model_template

    ModelTemplateList().unregister_model_template(model_template_id=model_template.model_template_id)


@pytest.fixture
def fxt_dataset_task(fxt_ote_id, fxt_model_template_dataset):
    yield TaskNode(
        title="Sample dataset task",
        task_properties=TaskProperties.from_model_template(fxt_model_template_dataset),
        project_id=ID(fxt_ote_id()),
        id_=ID(fxt_ote_id(1)),
    )


@pytest.fixture
def fxt_detection_task(fxt_ote_id, fxt_empty_project):
    yield TaskNode(
        title="dummy detection task",
        task_properties=TaskProperties.from_model_template(ModelTemplateList().get_by_id("detection")),
        project_id=fxt_ote_id(),
        id_=fxt_ote_id(2),
    )


@pytest.fixture
def fxt_model_storage_detection(fxt_empty_project, fxt_model_template_detection, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_empty_project.id_,
        task_node_id=fxt_mongo_id(6),
        model_template=fxt_model_template_detection,
    )


@pytest.fixture
def fxt_model_storage(fxt_model_storage_detection):
    yield fxt_model_storage_detection


@pytest.fixture
def fxt_classification_task(fxt_ote_id, fxt_model_storage_classification):
    yield TaskNode(
        title="dummy classification task",
        task_properties=TaskProperties.from_model_template(ModelTemplateList().get_by_id("classification")),
        project_id=fxt_ote_id(),
        id_=fxt_ote_id(3),
    )
