# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import itertools
from typing import cast

import pytest

from tests.mock_tasks import register_classification_task, register_detection_task
from tests.test_helpers import auto_wire_task_chain

from geti_types import CTX_SESSION_VAR, ID
from iai_core.algorithms import ModelTemplateList
from iai_core.entities.active_model_state import ActiveModelState
from iai_core.entities.label_schema import LabelSchemaView
from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.project import Project
from iai_core.entities.task_node import TaskNode, TaskProperties
from iai_core.repos import ActiveModelStateRepo, LabelRepo, LabelSchemaRepo, ModelStorageRepo, ProjectRepo, TaskNodeRepo
from iai_core.utils.deletion_helpers import DeletionHelpers
from iai_core.utils.project_factory import ProjectFactory


@pytest.fixture(scope="function")
def fxt_pipeline_project(
    request,
    fxt_empty_project_persisted,
    fxt_classification_labels_persisted,
) -> Project:
    model_template = register_classification_task(request)

    task_node = TaskNode(
        title="classification",
        project_id=fxt_empty_project_persisted.id_,
        task_properties=TaskProperties.from_model_template(model_template),
        id_=TaskNodeRepo.generate_id(),
    )
    TaskNodeRepo(fxt_empty_project_persisted.identifier).save(task_node)

    model_storage = ModelStorage(
        id_=ModelStorageRepo.generate_id(),
        project_id=fxt_empty_project_persisted.id_,
        task_node_id=task_node.id_,
        model_template=model_template,
    )
    ModelStorageRepo(fxt_empty_project_persisted.identifier).save(model_storage)

    active_model_state = ActiveModelState(
        task_node_id=task_node.id_,
        active_model_storage=model_storage,
    )
    ActiveModelStateRepo(fxt_empty_project_persisted.identifier).save(instance=active_model_state)

    fxt_empty_project_persisted.task_graph.add_node(task_node)
    ProjectRepo().save(fxt_empty_project_persisted)

    task_node_labels = fxt_classification_labels_persisted(fxt_empty_project_persisted.identifier)
    task_label_schema = cast(
        "LabelSchemaView",
        LabelSchemaView.from_labels(labels=task_node_labels, task_node_id=task_node.id_),
    )
    label_schema_repo = LabelSchemaRepo(fxt_empty_project_persisted.identifier)
    label_schema_repo.save(task_label_schema)

    return fxt_empty_project_persisted


@pytest.fixture
def fxt_task_chain_project(
    request,
    fxt_task_graph_three_nodes,
    fxt_model_templates_three_nodes,
):
    project = ProjectFactory.create_project_with_task_graph(
        name="__Test product inspection mock pipeline",
        description="",
        creator_id="dummy_user",
        task_graph=fxt_task_graph_three_nodes,
        model_templates=fxt_model_templates_three_nodes,
    )

    return ProjectRepo().get_by_id(project.id_)


@pytest.fixture(scope="function")
def fxt_configuration_dict(fxt_task_chain_project):
    return {
        "global": [
            {
                "entity_identifier": {
                    "component": "COORDINATOR",
                    "project_id": "615f02febd1e3319ccc52811",
                    "type": "COMPONENT_PARAMETERS",
                    "workspace_id": "615da7fec62d43b3c884ef19",
                },
                "parameters": [{"name": "auto_training", "value": True}],
                "type": "CONFIGURABLE_PARAMETERS",
            }
        ],
        "task_chain": [
            {
                "components": [
                    {
                        "entity_identifier": {
                            "model_storage_id": "615f02febd1e3319ccc52813",
                            "type": "HYPER_PARAMETERS",
                            "workspace_id": "615da7fec62d43b3c884ef19",
                        },
                        "groups": [
                            {
                                "name": "data_augmentation",
                                "parameters": [
                                    {"name": "auto_augment", "value": "None"},
                                    {"name": "rotation_range", "value": 90},
                                    {"name": "scaling_range", "value": 0.2},
                                ],
                                "type": "PARAMETER_GROUP",
                            },
                        ],
                        "type": "CONFIGURABLE_PARAMETERS",
                    },
                ]
            }
        ],
    }


@pytest.fixture(scope="function")
def fxt_detection_node(request, fxt_mongo_id):
    detection_template = register_detection_task(request)
    return TaskNode(
        title="Object detection (MOCK)",
        project_id=ID(),
        task_properties=TaskProperties.from_model_template(detection_template),
        id_=fxt_mongo_id(100),
    )


@pytest.fixture(scope="function")
def fxt_crop_node(fxt_mongo_id):
    model_template = ModelTemplateList().get_by_id("crop")
    return TaskNode(
        title="Crop (MOCK)",
        task_properties=TaskProperties.from_model_template(model_template),
        project_id=ID(),
        id_=fxt_mongo_id(101),
    )


@pytest.fixture(scope="function")
def fxt_classification_node(request, fxt_mongo_id):
    classification_template = register_classification_task(request)
    return TaskNode(
        title="Classification (MOCK)",
        project_id=ID(),
        task_properties=TaskProperties.from_model_template(classification_template),
        id_=fxt_mongo_id(102),
    )


@pytest.fixture(scope="function")
def fxt_task_graph_three_nodes(fxt_detection_node, fxt_crop_node, fxt_classification_node):
    return auto_wire_task_chain(task_nodes=[fxt_detection_node, fxt_crop_node, fxt_classification_node])


@pytest.fixture(scope="function")
def fxt_model_templates_three_nodes(
    fxt_model_template_detection,
    fxt_model_template_crop,
    fxt_model_template_classification,
):
    return [
        fxt_model_template_detection,
        fxt_model_template_crop,
        fxt_model_template_classification,
    ]


@pytest.fixture(scope="function")
def fxt_test_dataset_manager_data(
    fxt_detection_labels,
    fxt_detection_node,
    fxt_detection_label_schema,
    fxt_crop_node,
    fxt_classification_labels_good_bad,
    fxt_classification_node,
    fxt_classification_label_schema_good_bad,
    fxt_task_graph_three_nodes,
    fxt_model_templates_three_nodes,
    request,
):
    class ProjectNodesLabels:
        def __init__(
            self,
            d_labels,
            d_node,
            d_node_schema,
            cr_node,
            cl_labels,
            cl_node,
            cl_node_schema,
            project,
        ) -> None:
            self.detection_labels = d_labels
            self.detection_node = d_node
            self.detection_node_label_schema = d_node_schema
            self.crop_node = cr_node
            self.classification_labels = cl_labels
            self.classification_node = cl_node
            self.classification_node_label_schema = cl_node_schema
            self.project: Project = project

    # Save project
    CTX_SESSION_VAR.get().workspace_id
    project = ProjectFactory.create_project_with_task_graph(
        name="__Test dataset manager",
        creator_id="dummy_user",
        description="",
        task_graph=fxt_task_graph_three_nodes,
        model_templates=fxt_model_templates_three_nodes,
    )
    request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))

    # Save labels
    label_repo = LabelRepo(project.identifier)
    for label in itertools.chain(fxt_detection_labels, fxt_classification_labels_good_bad):
        label_repo.save(label)

    # Save schemas
    fxt_detection_label_schema._project_id = project.id_
    fxt_detection_label_schema._task_node_id = fxt_detection_node.id_
    fxt_classification_label_schema_good_bad._project_id = project.id_
    fxt_classification_label_schema_good_bad._task_node_id = fxt_classification_node.id_
    label_schema_repo = LabelSchemaRepo(project.identifier)
    label_schema_repo.save(fxt_detection_label_schema)
    label_schema_repo.save(fxt_classification_label_schema_good_bad)

    project = ProjectRepo().get_by_id(project.id_)
    return ProjectNodesLabels(
        d_labels=fxt_detection_labels,
        d_node=fxt_detection_node,
        d_node_schema=fxt_detection_label_schema,
        cr_node=fxt_crop_node,
        cl_labels=fxt_classification_labels_good_bad,
        cl_node=fxt_classification_node,
        cl_node_schema=fxt_classification_label_schema_good_bad,
        project=project,
    )
