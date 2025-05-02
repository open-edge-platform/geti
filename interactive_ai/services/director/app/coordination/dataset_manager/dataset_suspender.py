# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


"""
This module is responsible for suspending invalid dataset items when labels are added or removed
"""

import logging
from collections.abc import Sequence

from geti_types import ID, DatasetStorageIdentifier
from iai_core_py.entities.dataset_entities import TaskDataset
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.project import Project
from iai_core_py.repos import DatasetRepo, ProjectRepo, SuspendedAnnotationScenesRepo
from iai_core_py.repos.dataset_entity_repo import PipelineDatasetRepo
from iai_core_py.utils.dataset_helper import DatasetHelper

logger = logging.getLogger(__name__)


class DatasetSuspender:
    """
    This class is responsible for suspending invalid dataset items when labels are added or removed.
    """

    @staticmethod
    def suspend_dataset_items(
        suspended_scenes_descriptor_id: ID,
        workspace_id: ID,
        project_id: ID,
    ) -> None:
        """
        Suspend dataset items (by setting their `ignore_labels` flag appropriately)
        for a list of affected annotation_scene_ids. This typically happens after
        changing the label schema of a project, because it could happen that the
        new labels are relevant for already annotated images, but the user
        hasn't updated the annotations yet.

        This method deletes the descriptor after consuming it.

        :param suspended_scenes_descriptor_id: ID of the SuspendedAnnotationScenesDescriptor that contains information
        on suspended scenes
        :param workspace_id: ID of the workspace the project is in
        :param project_id: ID of the project for which annotations are suspended
        """
        project = ProjectRepo().get_by_id(project_id)
        dataset_storage = project.get_training_dataset_storage()
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage.id_,
        )
        suspended_annotations_repo = SuspendedAnnotationScenesRepo(dataset_storage_identifier)
        suspended_annotations_descriptor = suspended_annotations_repo.get_by_id(suspended_scenes_descriptor_id)
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage.identifier)

        for task_node in project.get_trainable_task_nodes():
            DatasetSuspender.suspend_items_by_annotation_scene_ids_for_task(
                annotation_scene_ids=suspended_annotations_descriptor.scenes_ids,
                task_dataset_entity=pipeline_dataset_entity.task_datasets[task_node.id_],
                project=project,
                dataset_storage=dataset_storage,
            )

        suspended_annotations_repo.delete_by_id(suspended_annotations_descriptor.id_)

    @staticmethod
    def suspend_items_by_annotation_scene_ids_for_task(
        annotation_scene_ids: Sequence[ID],
        task_dataset_entity: TaskDataset,
        project: Project,
        dataset_storage: DatasetStorage,
    ) -> None:
        """
        Suspend dataset items (by setting their `ignore_labels` flag appropriately)
        for a list of affected annotation_scene_ids.

        This method is called upon changes to the label schema of the project.

        :param annotation_scene_ids: List of IDs of the annotation scenes for which
            dataset items should be suspended.
        :param task_dataset_entity: TaskDataset containing the dataset for the task
        :param project: Project to which the task belongs
        :param dataset_storage: DatasetStorage containing the dataset items and annotations
        """
        dataset = task_dataset_entity.get_dataset(dataset_storage=dataset_storage)
        logger.info(
            "Suspending dataset items in dataset of %d samples, generated from "
            "previous training dataset. Suspending items for %d annotation scenes.",
            len(dataset),
            len(annotation_scene_ids),
        )
        # Perform suspension of dataset items
        for item in dataset:
            ignored_label_ids = DatasetHelper.compute_dataset_item_ignored_label_ids(
                item=item,
                project=project,
                dataset_storage=dataset_storage,
                annotation_scene_ids=annotation_scene_ids,
            )
            if ignored_label_ids:
                DatasetRepo(dataset_storage.identifier).save_ignored_label_ids_for_dataset_item(
                    dataset_id=dataset.id_,
                    dataset_item_id=item.id_,
                    label_ids=ignored_label_ids,
                )
