# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


"""
This module contains classes that keep track of the number of dataset items for a task.
"""

import logging
from typing import TYPE_CHECKING

from entities.dataset_item_count import (
    DatasetItemCount,
    DeletedDatasetItemCountData,
    LabelData,
    NewDatasetItemCountData,
    NullDatasetItemCount,
)
from entities.dataset_item_labels import DatasetItemLabels, NullDatasetItemLabels
from service.label_schema_service import LabelSchemaService
from storage.repos import DatasetItemCountRepo, DatasetItemLabelsRepo

from geti_kafka_tools import publish_event
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier
from iai_core_py.entities.label import Label
from iai_core_py.entities.subset import Subset
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.repos import DatasetRepo, ProjectRepo
from iai_core_py.utils.dataset_helper import DatasetHelper

if TYPE_CHECKING:
    from iai_core_py.entities.dataset_item import DatasetItem
    from iai_core_py.repos.mappers import CursorIterator


REQUIRED_ANOMALOUS_IMAGES_FIRST_TRAINING = 3
ASSIGNED_SUBSETS = [Subset.TRAINING, Subset.VALIDATION, Subset.TESTING]

logger = logging.getLogger(__name__)


class DatasetCounterUseCase:
    """
    This class is responsible for updating the DatasetItemCount, that stores information about the current training
    dataset in the DatasetItemCountRepo. The dataset item count is updated incrementally whenever a message is received
    that informs the director of an update in the training dataset.
    """

    @staticmethod
    def on_project_create(workspace_id: ID, project_id: ID) -> None:
        """
        When the project is created, initiate an empty count if there is none yet.

        :param workspace_id: ID of the workspace the project lives in
        :param project_id: ID of the created project
        """
        project = ProjectRepo().get_by_id(project_id)
        dataset_storage_id = project.training_dataset_storage_id
        for task_node in project.get_trainable_task_nodes():
            task_labels = LabelSchemaService.get_latest_labels_for_task(
                project_identifier=project.identifier,
                task_node_id=task_node.id_,
                include_empty=False,
            )
            dataset_storage_identifier = DatasetStorageIdentifier(
                workspace_id=workspace_id,
                project_id=project.id_,
                dataset_storage_id=dataset_storage_id,
            )
            dataset_item_count_repo = DatasetItemCountRepo(
                dataset_storage_identifier=dataset_storage_identifier,
            )
            dataset_item_count = dataset_item_count_repo.get_by_id(id_=task_node.id_)
            if isinstance(dataset_item_count, NullDatasetItemCount):
                dataset_item_count = DatasetCounterUseCase._initiate_empty_count(
                    task_node_id=task_node.id_, task_labels=task_labels
                )
                dataset_item_count_repo.save(dataset_item_count)

    @staticmethod
    def on_project_update(workspace_id: ID, project_id: ID) -> None:
        """
        When the project is updated, check if any labels were added or deleted. If any were added or deleted, update
        the "n_dataset_items_per_label" and "label_data" attributes to reflect this change.

        :param workspace_id: ID of the workspace the project lives in
        :param project_id: ID of the project that was updated
        """
        project = ProjectRepo().get_by_id(project_id)
        dataset_storage_id = project.training_dataset_storage_id
        trainable_task_nodes = [task for task in project.tasks if task.task_properties.is_trainable]
        for task_node in trainable_task_nodes:
            task_labels = LabelSchemaService.get_latest_labels_for_task(
                project_identifier=project.identifier,
                task_node_id=task_node.id_,
                include_empty=False,
            )
            dataset_item_count_repo = DatasetItemCountRepo(
                dataset_storage_identifier=DatasetStorageIdentifier(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    dataset_storage_id=dataset_storage_id,
                ),
            )
            dataset_item_count = dataset_item_count_repo.get_by_id(id_=task_node.id_)
            if isinstance(dataset_item_count, NullDatasetItemCount):
                DatasetCounterUseCase._initiate_empty_count(task_node_id=task_node.id_, task_labels=task_labels)
            else:
                task_label_ids = {label.id_ for label in task_labels}
                counter_label_ids = {label.id_ for label in dataset_item_count.task_label_data}
                added_labels = task_label_ids - counter_label_ids
                deleted_labels = counter_label_ids - task_label_ids
                for label_id in added_labels:
                    dataset_item_count.n_items_per_label[label_id] = 0
                for label_id in deleted_labels:
                    del dataset_item_count.n_items_per_label[label_id]
                if added_labels or deleted_labels:
                    logger.debug("Updated dataset item count for new label schema")
                dataset_item_count.task_label_data = [LabelData.from_label(label) for label in task_labels]
            dataset_item_count_repo.save(dataset_item_count)

    @staticmethod
    def on_dataset_update(
        workspace_id: ID,
        project_id: ID,
        task_node_id: ID,
        dataset_id: ID,
        new_dataset_items: list[ID],
        deleted_dataset_items: list[ID],
        assigned_dataset_items: list[ID],
    ) -> None:
        """
        Update the dataset counters for a task when the dataset is updated, and publish a message that the dataset
        counters are updated. Steps taken:
        - If the DatasetItemCount is not there yet, create an empty count
        - Update the count with the added, deleted and assigned items
        - Save the new DatasetItemCount
        - Publish a 'dataset_counters_updated' message to inform the AutoTrainUseCase that it should check training
        requirements.

        :param workspace_id: Workspace the project and task live in
        :param project_id: Project to update the dataset counter for
        :param task_node_id: Task to update the dataset counter for
        :param dataset_id: ID of the training dataset for the task
        :param new_dataset_items: List of all dataset items that were added to the training dataset
        :param deleted_dataset_items: List of all items that were deleted from the training dataset
        :param assigned_dataset_items: List of all dataset items in the training dataset that were assigned a subset
        """
        project = ProjectRepo().get_by_id(project_id)
        dataset_storage = project.get_training_dataset_storage()
        task_node = next(task for task in project.tasks if task.id_ == task_node_id)
        task_labels = LabelSchemaService.get_latest_labels_for_task(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
            include_empty=False,
        )
        task_label_ids = [label.id_ for label in task_labels]

        dataset_item_count_repo = DatasetItemCountRepo(
            dataset_storage_identifier=DatasetStorageIdentifier(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage.id_,
            ),
        )
        if not dataset_item_count_repo.exists(id_=task_node.id_):
            dataset_item_count = DatasetCounterUseCase._initiate_empty_count(
                task_node_id=task_node.id_, task_labels=task_labels
            )
            dataset_item_count_repo.save(dataset_item_count)

        new_dataset_item_count_data = DatasetCounterUseCase._process_new_items(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=task_node,
            task_label_ids=task_label_ids,
            dataset_id=dataset_id,
            new_item_ids=new_dataset_items,
        )
        deleted_dataset_item_count_data = DatasetCounterUseCase._process_deleted_items(
            dataset_storage_identifier=dataset_storage.identifier,
            deleted_item_ids=deleted_dataset_items,
        )
        dataset_item_count_repo.update_count_data(
            id_=task_node.id_,
            new_dataset_item_count_data=new_dataset_item_count_data,
            deleted_dataset_item_count_data=deleted_dataset_item_count_data,
            assigned_dataset_items=assigned_dataset_items,
        )
        publish_event(
            topic="dataset_counters_updated",
            body={"workspace_id": str(workspace_id), "project_id": str(project.id_)},
            key=str(project_id).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

    @staticmethod
    def _process_new_items(
        dataset_storage_identifier: DatasetStorageIdentifier,
        task_node: TaskNode,
        task_label_ids: list[ID],
        dataset_id: ID,
        new_item_ids: list[ID],
    ) -> NewDatasetItemCountData:
        """
        This method returns a NewDatasetItemCountData with the newly added dataset items.
        Performs the following steps:
            - Add the new items to the 'NewDatasetItemCountData.count'
            - Add the new dataset items with their labels to the DatasetItemLabelsRepo
            - Add the new dataset items IDs to the 'NewDatasetItemCountData.dataset_items_ids' list
            - Add the new per label dataset item count to the 'NewDatasetItemCountData.dataset_items_ids' dictionary

        :param dataset_storage_identifier: Identifier of the dataset storage containing the dataset items
        :param task_node: TaskNode for which the dataset items are counted
        :param dataset_id: ID of the training dataset
        :param new_item_ids: List of newly added dataset item IDs
        :return: a NewDatasetItemCountData
        """
        dataset_repo = DatasetRepo(dataset_storage_identifier)
        new_dataset_items: list[DatasetItem] | CursorIterator[DatasetItem] = []
        if new_item_ids:
            new_dataset_items = dataset_repo.get_items_from_dataset(
                dataset_id=dataset_id, dataset_item_ids=new_item_ids
            )
        # Initiate list for the labels per dataset item to save in the DatasetItemLabelsRepo
        dataset_item_labels_to_save = []
        new_dataset_items_count = 0
        new_unassigned_dataset_items = []
        new_items_per_label_count: dict[ID, int] = {}
        for new_dataset_item in new_dataset_items:
            # Do not count dataset items with the empty label
            if len(new_dataset_item.get_roi_label_ids(include_empty=True)) - len(
                new_dataset_item.get_roi_label_ids(include_empty=False)
            ):
                continue
            # Increment the total and unassigned count by 1 for every new item
            new_dataset_items_count += 1
            if new_dataset_item.subset not in ASSIGNED_SUBSETS:
                new_unassigned_dataset_items.append(new_dataset_item.id_)

            item_label_ids = DatasetHelper.get_dataset_item_label_ids(
                item=new_dataset_item, is_task_global=task_node.task_properties.is_global, include_empty=False
            )
            # Filter labels for the task
            label_ids = [label_id for label_id in task_label_ids if label_id in item_label_ids]

            # Store the labels for the new item in the DatasetItemLabelsRepo
            dataset_item_labels_to_save.append(
                DatasetItemLabels(
                    dataset_item_id=new_dataset_item.id_,
                    label_ids=label_ids,
                )
            )

            # Increment the per-label counter by 1 for every label in the item
            for label_id in label_ids:
                if new_items_per_label_count.get(label_id) is None:
                    new_items_per_label_count[label_id] = 0
                new_items_per_label_count[label_id] += 1

        if dataset_item_labels_to_save:
            DatasetItemLabelsRepo(dataset_storage_identifier).save_many(instances=dataset_item_labels_to_save)

        return NewDatasetItemCountData(
            count=new_dataset_items_count,
            dataset_item_ids=new_unassigned_dataset_items,
            per_label_count=new_items_per_label_count,
        )

    @staticmethod
    def _process_deleted_items(
        dataset_storage_identifier: DatasetStorageIdentifier,
        deleted_item_ids: list[ID],
    ) -> DeletedDatasetItemCountData:
        """
        This method returns a DeletedDatasetItemCountDat with the deleted dataset items.
        Performs the following steps:
            - Add the deleted items to 'DeletedDatasetItemCountData.count'
            - Fetch and delete the dataset item labels from the DatasetItemLabels and subtract one from the
            'n_items_per_label' for each of those labels.
            - Add the deleted dataset items IDs to the 'DeletedDatasetItemCountData.dataset_items_ids' list
            - Add the deleted per label dataset item count to the 'DeletedDatasetItemCountData.dataset_items_ids'
            dictionary

        :param dataset_storage_identifier: Identifier of the dataset storage containing the dataset items
        :param deleted_item_ids: List of deleted dataset item IDs
        :return: a DeletedDatasetItemCountData
        """
        dataset_item_labels_repo = DatasetItemLabelsRepo(dataset_storage_identifier)
        deleted_dataset_items_count = 0
        deleted_unassigned_dataset_items = []
        deleted_items_per_label_count: dict[ID, int] = {}
        for item_id in deleted_item_ids:
            dataset_item_labels = dataset_item_labels_repo.get_by_id(item_id)
            if not isinstance(dataset_item_labels, NullDatasetItemLabels):
                for label in dataset_item_labels.label_ids:
                    if deleted_items_per_label_count.get(label) is None:
                        deleted_items_per_label_count[label] = 0
                    deleted_items_per_label_count[label] += 1
                deleted_dataset_items_count += 1
            deleted_unassigned_dataset_items.append(item_id)
            dataset_item_labels_repo.delete_by_id(item_id)
        return DeletedDatasetItemCountData(
            count=deleted_dataset_items_count,
            dataset_item_ids=deleted_unassigned_dataset_items,
            per_label_count=deleted_items_per_label_count,
        )

    @staticmethod
    def _initiate_empty_count(task_node_id: ID, task_labels: list[Label]) -> DatasetItemCount:
        """
        Initiate an empty DatasetItemCount from a list of labels for the task

        :param task_node_id: ID of the task node for which to initiate empty DatasetItemCount
        :param task_labels: Current labels for the task
        """
        logger.debug(
            "DatasetItemCount was not present for task %s- initialized empty dataset item count",
            task_node_id,
        )
        return DatasetItemCount(
            task_node_id=task_node_id,
            n_dataset_items=0,
            task_label_data=[LabelData.from_label(label) for label in task_labels],
            n_items_per_label={label.id_: 0 for label in task_labels},
            unassigned_dataset_items=[],
        )
