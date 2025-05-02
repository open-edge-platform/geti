# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


"""
This module is responsible for updating the training datasets when new annotations are added or the configuration is
updated.
"""

from collections.abc import Sequence
from functools import lru_cache

from service.label_schema_service import LabelSchemaService

from geti_kafka_tools import publish_event
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, MediaIdentifierEntity
from iai_core_py.entities.annotation import NullAnnotationScene
from iai_core_py.entities.dataset_entities import PipelineDataset
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.datasets import Dataset
from iai_core_py.entities.model_template import TaskFamily
from iai_core_py.entities.project import Project
from iai_core_py.entities.shapes import Rectangle
from iai_core_py.entities.subset import Subset
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.repos import AnnotationSceneRepo, DatasetRepo, ProjectRepo
from iai_core_py.repos.dataset_entity_repo import PipelineDatasetRepo
from iai_core_py.utils.dataset_helper import DatasetHelper
from iai_core_py.utils.flow_control import FlowControl


class DatasetUpdateUseCase:
    """
    This class is responsible for updating the training dataset whenever new annotations are added.
    """

    @staticmethod
    def update_dataset_with_new_annotation_scene(
        project_id: ID,
        annotation_scene_id: ID,
    ) -> None:
        """
        Updates the training dataset with a newly received annotation scene. Steps taken:
         - Get the project, workspace and dataset storage
         - Get the pipeline dataset and convert annotations to dataset items for the first task
         - For each trainable task, filter the dataset items for relevant items for that task and add them to the
         training dataset
         - For each flow control task, apply the flow control task to the dataset items from the previous task to
         create dataset items for the next task.

        :param project_id: Project for which the dataset is updated
        :param annotation_scene_id: ID of the new annotation scene
        """
        project = ProjectRepo().get_by_id(project_id)
        dataset_storage = DatasetUpdateUseCase._get_training_dataset_storage_for_project(project)
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage.identifier)
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        annotation_scene = ann_scene_repo.get_by_id(annotation_scene_id)
        item = DatasetHelper.annotation_scene_to_dataset_item(
            annotation_scene=annotation_scene,
            dataset_storage=dataset_storage,
            subset=Subset.UNASSIGNED,
        )
        new_items_dataset = Dataset(items=[item], id=DatasetRepo.generate_id())
        DatasetUpdateUseCase._update_dataset_with_new_items(
            new_items_dataset_for_task=new_items_dataset,
            pipeline_dataset_entity=pipeline_dataset_entity,
            project=project,
            dataset_storage_identifier=dataset_storage.identifier,
        )

    @staticmethod
    @lru_cache
    def _get_training_dataset_storage_for_project(project: Project) -> DatasetStorage:
        """
        Cached method to get the training dataset storage for a project. Necessary to increase speed for handling new
        annotation scene events.

        :param project: project to get training dataset storage for
        :return: training dataset storage
        """
        return project.get_training_dataset_storage()

    @staticmethod
    def _update_dataset_with_new_items(
        new_items_dataset_for_task: Dataset,
        pipeline_dataset_entity: PipelineDataset,
        project: Project,
        dataset_storage_identifier: DatasetStorageIdentifier,
    ) -> None:
        """
        Update the training dataset for each task with a list of new items. Loops over all tasks and takes the following
        steps for each task:
        Trainable tasks:
        - Filter the dataset, selecting only items that are relevant for that task
        - Compare the new dataset items with the previous ones, and if they are the same copy the subset from the
           previous dataset items
        - Remove all previous dataset items for the media that have new annotations
        - Add the new dataset items to the training dataset
        - Publish a message 'dataset_updated' that contains the added and deleted dataset items
        Flow control tasks:
        - Modify the dataset preparing the new dataset for the next task

        :param new_items_dataset_for_task: Dataset with new items to be added to the training datasets for the first
        task. For subsequent tasks, the new items dataset will be constructed using the flow control mechanism.
        :param pipeline_dataset_entity: PipelineDataset containing the training datasets
        :param project: Project for which dataset items are added
        :param dataset_storage_identifier: Identifier of the dataset storage containing the datasets and annotations
        """
        # Iterate over all the tasks

        prev_node: TaskNode | None = None
        for task_node in project.tasks:
            if task_node.task_properties.is_trainable:
                task_labels = LabelSchemaService.get_latest_labels_for_task(
                    task_node_id=task_node.id_,
                    project_identifier=project.identifier,
                    include_empty=True,
                )
                task_label_ids = [label.id_ for label in task_labels]

                task_dataset = pipeline_dataset_entity.task_datasets[task_node.id_]
                media_identifiers = [item.media_identifier for item in new_items_dataset_for_task]

                # Select only the dataset items relevant for the current task
                new_items_dataset_for_task = DatasetUpdateUseCase.filter_dataset(
                    dataset=new_items_dataset_for_task, task_label_ids=task_label_ids, task_node=task_node
                )

                # Compare the dataset items to the current dataset items, and in case nothing changed copy the subsets
                # of the previous dataset items
                current_dataset_items_for_task = task_dataset.get_dataset_items_for_media_identifiers(
                    media_identifiers=media_identifiers,
                    dataset_storage_identifier=dataset_storage_identifier,
                )
                DatasetUpdateUseCase._set_subset_for_already_existing_annotations(
                    media_identifiers=media_identifiers,
                    current_dataset_items_for_task=current_dataset_items_for_task,
                    new_items_dataset_for_task=new_items_dataset_for_task,
                    task_label_ids=task_label_ids,
                )
                # Remove the previous dataset items and replace them with the new ones.
                deleted_items = task_dataset.remove_items_for_media_identifiers(
                    media_identifiers=media_identifiers,
                    dataset_storage_identifier=dataset_storage_identifier,
                )
                task_dataset.add_dataset(
                    new_dataset=new_items_dataset_for_task,
                    dataset_storage_identifier=dataset_storage_identifier,
                )
                new_items_string = [str(item.id_) for item in new_items_dataset_for_task]
                deleted_items_string = [str(deleted_item) for deleted_item in deleted_items]
                publish_event(
                    topic="dataset_updated",
                    body={
                        "workspace_id": str(project.workspace_id),
                        "project_id": str(project.id_),
                        "task_node_id": str(task_node.id_),
                        "dataset_id": str(task_dataset.dataset_id),
                        "new_dataset_items": new_items_string,
                        "deleted_dataset_items": deleted_items_string,
                        "assigned_dataset_items": [],
                    },
                    key=str(task_node.id_).encode(),
                    headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
                )

            elif task_node.task_properties.task_family == TaskFamily.FLOW_CONTROL:
                new_items_dataset_for_task = FlowControl.flow_control(
                    project=project,
                    task_node=task_node,
                    prev_task_node=prev_node,
                    dataset=new_items_dataset_for_task,
                    subset=Subset.UNASSIGNED,
                )
            prev_node = task_node

    @staticmethod
    def _set_subset_for_already_existing_annotations(
        media_identifiers: Sequence[MediaIdentifierEntity],
        current_dataset_items_for_task: Sequence[DatasetItem],
        new_items_dataset_for_task: Dataset,
        task_label_ids: Sequence[ID],
    ) -> None:
        """
        This method compares the new dataset items for a task with the previously existing dataset items for that task.
        If the annotations for the task are the same as they were previously, the new dataset items copy the
        subset from the previous dataset items, so that the dataset management can recognize whether or not these items
        were previously trained.

        :param media_identifiers: Media identifiers to filter the dataset items
        :param current_dataset_items_for_task: Currently stored dataset items for the media identifiers for this task
        :param new_items_dataset_for_task: New dataset items for the media identifiers for this task
        :param task_label_ids: Relevant label ID's for the task.
        """

        task_label_ids_set = set(task_label_ids)
        # Create a mapping from every media identifier to the new and previous dataset items
        media_identifier_to_previous_dataset_items: dict[MediaIdentifierEntity, list[DatasetItem]] = {}
        media_identifier_to_new_dataset_items: dict[MediaIdentifierEntity, list[DatasetItem]] = {}
        for item in current_dataset_items_for_task:
            if item.media_identifier not in media_identifier_to_previous_dataset_items:
                media_identifier_to_previous_dataset_items[item.media_identifier] = []
            media_identifier_to_previous_dataset_items[item.media_identifier].append(item)
        for item in new_items_dataset_for_task:
            if item.media_identifier not in media_identifier_to_new_dataset_items:
                media_identifier_to_new_dataset_items[item.media_identifier] = []
            media_identifier_to_new_dataset_items[item.media_identifier].append(item)
        # Loop over the media identifiers and update the subset of those that have the same annotations for the task
        for media_identifier in set(media_identifiers):
            new_dataset_items_for_media = media_identifier_to_new_dataset_items.get(media_identifier, [])
            previous_dataset_items_for_media = media_identifier_to_previous_dataset_items.get(media_identifier, [])
            previous_annotation_scene_for_identifier = next(
                (item.annotation_scene for item in previous_dataset_items_for_media),
                NullAnnotationScene(),
            )
            new_annotation_scene_for_identifier = next(
                (item.annotation_scene for item in new_dataset_items_for_media),
                NullAnnotationScene(),
            )
            old_annotation_ids_for_current_task = {
                annotation.id_
                for annotation in previous_annotation_scene_for_identifier.annotations
                if not annotation.get_label_ids(include_empty=True).isdisjoint(task_label_ids_set)
            }
            new_annotation_ids_for_current_task = {
                annotation.id_
                for annotation in new_annotation_scene_for_identifier.annotations
                if not annotation.get_label_ids(include_empty=True).isdisjoint(task_label_ids_set)
            }
            if new_annotation_ids_for_current_task == old_annotation_ids_for_current_task:
                for new_dataset_item in new_dataset_items_for_media:
                    # Find the item that is the same dataset item by searching for the item with the same ROI (either
                    # having the same ROI ID or both being a full box ROI), and copy the subset from that item.
                    new_dataset_item.subset = next(
                        (
                            old_dataset_item.subset
                            for old_dataset_item in previous_dataset_items_for_media
                            if old_dataset_item.roi.id_ == new_dataset_item.roi.id_
                            or (
                                Rectangle.is_full_box(old_dataset_item.roi.shape)
                                and Rectangle.is_full_box(new_dataset_item.roi.shape)
                            )
                        ),
                        Subset.UNASSIGNED,
                    )

    @staticmethod
    def filter_dataset(dataset: Dataset, task_label_ids: list[ID], task_node: TaskNode) -> Dataset:
        """
        Filters out dataset items which have no label pertaining to a given task by selecting the items whose labels
        overlap with the task labels.

        :param dataset: the dataset to be filtered
        :param task_node: the significant task
        :param task_label_ids: List of label ids for the task.
        :return: the filtered dataset
        """
        indices_to_remove = [
            idx
            for idx, item in enumerate(dataset)
            if len(
                DatasetHelper.get_dataset_item_label_ids(
                    item=item,
                    task_label_ids=task_label_ids,
                    is_task_global=task_node.task_properties.is_global,
                    include_empty=True,
                )
            )
            == 0
        ]
        dataset.remove_at_indices(indices_to_remove)
        return dataset

    @staticmethod
    def delete_media_from_datasets(project_id: ID, media_id: ID) -> None:
        """
        Delete all dataset items related to a media item from the training dataset and publish an event to indicate
        that the dataset has been updated.

        :param project_id: ID of the project
        :param media_id: ID of the deleted media
        """
        project = ProjectRepo().get_by_id(project_id)
        dataset_storage = project.get_training_dataset_storage()
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage.identifier)
        for (
            task_node_id,
            task_dataset_entity,
        ) in pipeline_dataset_entity.task_datasets.items():
            deleted_items = task_dataset_entity.remove_items_for_media(
                media_id=media_id, dataset_storage_identifier=dataset_storage.identifier
            )
            deleted_dataset_items_string = [str(deleted_item) for deleted_item in deleted_items]
            publish_event(
                topic="dataset_updated",
                body={
                    "workspace_id": str(CTX_SESSION_VAR.get().workspace_id),
                    "project_id": str(project.id_),
                    "task_node_id": str(task_node_id),
                    "dataset_id": str(task_dataset_entity.dataset_id),
                    "new_dataset_items": [],
                    "deleted_dataset_items": deleted_dataset_items_string,
                    "assigned_dataset_items": [],
                },
                key=str(task_node_id).encode(),
                headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
            )
