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
import logging

from _pytest.fixtures import FixtureRequest

from communication.constants import MAX_UNANNOTATED_DATASET_SIZE
from tests.utils.test_helpers import register_model_template_from_dict

from geti_kafka_tools import publish_event
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier
from sc_sdk.entities.annotation import AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_entities import TaskDataset
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.model_template import ModelTemplate
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_graph import TaskEdge, TaskGraph
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import AnnotationSceneRepo, DatasetRepo, LabelSchemaRepo, ProjectRepo
from sc_sdk.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from sc_sdk.utils.media_factory import Media2DFactory

logger = logging.getLogger(__name__)


def auto_wire_task_chain(task_nodes: list[TaskNode]) -> TaskGraph:
    """
    Make a TaskGraph with a linear task chain, based on order of task_nodes.
    It'll automatically find the ports and create the edges, based on the given data_type.

    :param task_nodes: List of TaskNode to chain
    :return: TaskGraph
    """
    task_graph = TaskGraph()
    for i in range(max(len(task_nodes) - 1, 0)):
        from_task = task_nodes[i]
        to_task = task_nodes[i + 1]

        task_edge = TaskEdge(from_task=from_task, to_task=to_task)
        task_graph.add_task_edge(task_edge)

    return task_graph


def register_anomaly_model_template(
    test_case: FixtureRequest,
) -> ModelTemplate:
    """
    Register anomaly detection model template.
    """
    model_template = {
        "task_family": "VISION",
        "task_type": "ANOMALY_DETECTION",
        "model_template_id": "anomaly",
        "model_template_path": "",
        "name": "Anomaly Detection",
        "is_trainable": True,
        "task_type_sort_priority": 1,
        "instantiation": "GRPC",
        "exportable_code_paths": {"default": "$EXPORTABLE_CODE_ROOT/torch_anomaly"},
        "model_optimization_methods": [],
        "grpc_address": "localhost:50059",
        "hyper_parameters": {"base_path": "hyper_parameters.yaml"},
        "dataset_requirements": {"classes": ["Normal", "Anomalous"]},
    }

    return register_model_template_from_dict(test_case, model_template)


def _repo_cleanup():
    """
    Clean up workspace completely, including .
    """

    def _cleanup():
        project_repo: ProjectRepo = ProjectRepo()
        for project in project_repo.get_all():
            DeletionHelpers.delete_project_by_id(project_id=project.id_)

    return _cleanup


def get_unannotated_dataset(
    project: Project,
    dataset_storage: DatasetStorage,
    max_dataset_size: int | None = None,
) -> Dataset:
    """
    Retrieve a dataset made out of the media without annotations.
    :param project: Project for which to get the unannotated dataset
    :param dataset_storage: DatasetStorage containing the dataset items, annotations and media.
    :param max_dataset_size: Optional, max number of items in the dataset.
        If None, it caps at 10k elements.
    :return: dataset of unannotated items
    """

    if max_dataset_size is None:
        max_dataset_size = MAX_UNANNOTATED_DATASET_SIZE

    num_unannotated_ids_to_fetch = max_dataset_size

    unannotated_identifiers = tuple(
        AnnotationSceneStateHelper.get_unannotated_media_identifiers_in_dataset_storage(
            dataset_storage_identifier=dataset_storage.identifier,
            project=project,
            max_unseen_media=num_unannotated_ids_to_fetch,
        )
    )

    dataset = Dataset(id=DatasetRepo.generate_id())
    for identifier in unannotated_identifiers:
        media = Media2DFactory().get_media_for_identifier(
            identifier, dataset_storage_identifier=dataset_storage.identifier
        )
        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.INTERMEDIATE,
            media_identifier=identifier,
            media_height=media.height,
            media_width=media.width,
            id_=AnnotationSceneRepo.generate_id(),
        )
        item = DatasetItem(
            media=media,
            annotation_scene=annotation_scene,
            id_=DatasetRepo.generate_id(),
        )
        dataset.append(item)
    return dataset


def construct_and_save_train_dataset_for_task(
    task_dataset_entity: TaskDataset,
    project_id: ID,
    task_node: TaskNode,
    dataset_storage: DatasetStorage,
) -> Dataset:
    """
    This method does the following:
    1. Fetches the current dataset from the task dataset entity
    2. Calls the subset manager to set the unassigned subsets in the dataset
    3. Save the new subsets to the repo by calling update_subsets and publish that the subsets were updated
    4. Makes a copy of the dataset and passes it to the training operator

    :param task_dataset_entity: TaskDataset that holds the current dataset for the task
    :param project_id: ID of the project
    :param task_node: Task node for which the dataset is fetched
    :param dataset_storage: DatasetStorage containing the dataset items
    :return: A copy of the current dataset, split into subsets.
    """
    workspace_id = CTX_SESSION_VAR.get().workspace_id
    project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
    task_label_schema = LabelSchemaRepo(project_identifier).get_latest_view_by_task(task_node_id=task_node.id_)

    dataset = task_dataset_entity.get_dataset(dataset_storage=dataset_storage)

    task_dataset_entity.save_subsets(dataset=dataset, dataset_storage_identifier=dataset_storage.identifier)
    assigned_items_list_string = [str(assigned_item.id_) for assigned_item in dataset]
    publish_event(
        topic="dataset_updated",
        body={
            "workspace_id": str(workspace_id),
            "project_id": str(project_id),
            "task_node_id": str(task_node.id_),
            "dataset_id": str(task_dataset_entity.dataset_id),
            "new_dataset_items": [],
            "deleted_dataset_items": [],
            "assigned_dataset_items": assigned_items_list_string,
        },
        key=str(task_node.id_).encode(),
    )
    for item in dataset:
        item.id_ = DatasetRepo.generate_id()
    new_training_dataset = Dataset(
        items=list(dataset),
        purpose=DatasetPurpose.TRAINING,
        label_schema_id=task_label_schema.id_,
        id=DatasetRepo.generate_id(),
    )
    DatasetRepo(dataset_storage.identifier).save_deep(new_training_dataset)
    return new_training_dataset
