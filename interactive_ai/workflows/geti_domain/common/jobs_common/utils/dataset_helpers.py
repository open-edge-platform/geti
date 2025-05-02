# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module defines helpers used to construct datasets"""

import copy
import os

from geti_kafka_tools import publish_event
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, ProjectIdentifier
from iai_core.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core.entities.annotation_scene_state import AnnotationState
from iai_core.entities.dataset_entities import TaskDataset
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.model_template import TaskType
from iai_core.entities.project import Project
from iai_core.entities.subset import Subset
from iai_core.entities.task_node import TaskNode
from iai_core.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, DatasetRepo, LabelSchemaRepo
from iai_core.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core.utils.dataset_helper import DatasetHelper
from iai_core.utils.flow_control import FlowControl
from iai_core.utils.iteration import grouper
from iai_core.utils.media_factory import Media2DFactory

from jobs_common.tasks.utils.progress import report_progress
from jobs_common.utils.subset_management.subset_manager import TaskSubsetManager

# Maximum recommended size for unannotated datasets
MAX_UNANNOTATED_DATASET_SIZE: int = 10000

# Maximum recommended size for training dataset
try:
    MAX_TRAINING_DATASET_SIZE: int | None = int(os.environ.get("MAX_TRAINING_DATASET_SIZE"))  # type: ignore[arg-type]
except (ValueError, TypeError):
    MAX_TRAINING_DATASET_SIZE = None
MAX_TRAINING_DATASET_SIZE_WARNING = (
    f"There are more than {MAX_TRAINING_DATASET_SIZE} annotated data available for training. "
    f"The free trial is limited to training with the first {MAX_TRAINING_DATASET_SIZE} annotated data."
)


class DatasetHelpers:
    """
    Implements helpers for dataset creation and manipulation in jobs
    """

    @staticmethod
    @unified_tracing
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
            media = Media2DFactory.get_media_for_identifier(
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

    @staticmethod
    @unified_tracing
    def _get_unannotated_dataset_for_cropped_task(
        dataset_storage_identifier: DatasetStorageIdentifier,
        task_id: ID,
        task_before_crop_id: ID,
        max_items: int | None = None,
    ) -> Dataset:
        """
        Build a dataset out of ROIs that are unannotated for a certain task following a crop one.

        :param dataset_storage_identifier: Identifier of the dataset storage
            containing the unannotated media to include in the output dataset
        :param task_id: ID of the task to get the unannotated dataset for
        :param task_before_crop_id: ID of the vision task before the crop one
        :param max_items: maximum number of items to add to the dataset
        :return: Dataset with ROIs that are unannotated for the task.
        """
        # Use the AnnotationSceneStateRepo to find the unannotated media for this task
        ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)
        unannotated_media_states = ann_scene_state_repo.get_all_by_state_for_task(
            matchable_annotation_states_per_task={
                task_before_crop_id: [
                    AnnotationState.ANNOTATED,
                    AnnotationState.PARTIALLY_ANNOTATED,
                ],
                task_id: [AnnotationState.NONE, AnnotationState.PARTIALLY_ANNOTATED],
            }
        )

        unannotated_dataset = Dataset(id=DatasetRepo.generate_id())
        ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
        n_items = 0
        for media_state in unannotated_media_states:
            # For each media unannotated for this task, create a new AnnotationScene
            # identical to the user annotation but with type INTERMEDIATE
            media = Media2DFactory.get_media_for_identifier(
                media_identifier=media_state.media_identifier,
                dataset_storage_identifier=dataset_storage_identifier,
            )
            user_annotation = ann_scene_repo.get_by_id(media_state.annotation_scene_id)
            prediction_scene = copy.deepcopy(user_annotation)
            prediction_scene.kind = AnnotationSceneKind.INTERMEDIATE
            prediction_scene.id_ = AnnotationSceneRepo.generate_id()
            ann_scene_repo.save(prediction_scene)
            # Create a DatasetItem for each ROI without annotations for this task
            for unannotated_roi_id in media_state.unannotated_rois[task_id]:
                item = DatasetItem(
                    id_=DatasetRepo.generate_id(),
                    media=media,
                    annotation_scene=prediction_scene,
                    roi=prediction_scene.get_annotation_with_annotation_id(unannotated_roi_id),
                )
                unannotated_dataset.append(item)
                n_items += 1
                if max_items is not None and n_items >= max_items:
                    return unannotated_dataset
        return unannotated_dataset

    @staticmethod
    @unified_tracing
    def get_unannotated_dataset_for_task(
        project: Project,
        dataset_storage: DatasetStorage,
        task_node: TaskNode,
        max_dataset_size: int | None = None,
    ) -> Dataset:
        """
        Build a dataset out of the media without annotations for a task.

        - If the task is the first one, it looks for media without any annotation.
        - If not the first task, it considers ROI which are annotated for the previous
          task but unannotated for this one.

        :param project: Project for which to get the unannotated dataset
        :param dataset_storage: DatasetStorage containing the dataset items, annotations and media.
        :param task_node: TaskNode to get the unannotated dataset for
        :param max_dataset_size: maximum number of items in the dataset
        :return: dataset of unannotated items
        """
        if not task_node.task_properties.is_trainable:
            raise ValueError("The task node must be trainable.")
        task_graph = project.task_graph
        immediate_previous_tasks = task_graph.get_immediate_previous_tasks(task_node)
        if not immediate_previous_tasks:
            raise RuntimeError(f"No previous task found for trainable task node {task_node.id_}")
        if len(immediate_previous_tasks) > 1:
            raise NotImplementedError("Chains where some tasks have multiple source tasks are not supported.")

        previous_task = immediate_previous_tasks[0]
        previous_task_is_crop = previous_task.task_properties.task_type == TaskType.CROP
        if previous_task_is_crop:
            task_before_crop = task_graph.get_immediate_previous_tasks(previous_task)[0]
            dataset = DatasetHelpers._get_unannotated_dataset_for_cropped_task(
                dataset_storage_identifier=dataset_storage.identifier,
                task_id=task_node.id_,
                task_before_crop_id=task_before_crop.id_,
                max_items=max_dataset_size,
            )
        else:
            dataset = DatasetHelpers.get_unannotated_dataset(
                project=project,
                dataset_storage=dataset_storage,
                max_dataset_size=max_dataset_size,
            )
        return dataset

    @staticmethod
    @unified_tracing
    def construct_and_save_train_dataset_for_task(
        task_dataset_entity: TaskDataset,
        project_id: ID,
        task_node: TaskNode,
        dataset_storage: DatasetStorage,
        max_training_dataset_size: int | None = None,
        reshuffle_subsets: bool = False,
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
        :param max_training_dataset_size: maximum training dataset size
        :param reshuffle_subsets: Whether to reassign/shuffle all the items to subsets including Test set from scratch
        :return: A copy of the current dataset, split into subsets.
        """
        workspace_id = CTX_SESSION_VAR.get().workspace_id
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
        task_label_schema = LabelSchemaRepo(project_identifier).get_latest_view_by_task(task_node_id=task_node.id_)

        dataset = task_dataset_entity.get_dataset(dataset_storage=dataset_storage)

        training_dataset_size = min(
            max_training_dataset_size if max_training_dataset_size is not None else len(dataset),
            len(dataset),
        )
        if MAX_TRAINING_DATASET_SIZE is not None and training_dataset_size > MAX_TRAINING_DATASET_SIZE:
            report_progress(warning=MAX_TRAINING_DATASET_SIZE_WARNING)
            training_dataset_size = MAX_TRAINING_DATASET_SIZE

        training_dataset_items = list(dataset[:training_dataset_size])

        if reshuffle_subsets:
            subsets_to_reset = (Subset.TRAINING, Subset.TESTING, Subset.VALIDATION)
        else:
            subsets_to_reset = None

        TaskSubsetManager.split(
            dataset_items=iter(training_dataset_items),
            task_node=task_node,
            subsets_to_reset=subsets_to_reset,
        )
        task_dataset_entity.save_subsets(dataset=dataset, dataset_storage_identifier=dataset_storage.identifier)

        assigned_items_list_string = [str(assigned_item.id_) for assigned_item in training_dataset_items]
        # Publish dataset update events in chunks of max 20 items, to avoid hitting the Kafka message size limit and
        # also to avoid excessive load on the consumer side.
        for assigned_items_chunk in grouper(assigned_items_list_string, chunk_size=20):
            publish_event(
                topic="dataset_updated",
                body={
                    "workspace_id": str(project_identifier.workspace_id),
                    "project_id": str(project_id),
                    "task_node_id": str(task_node.id_),
                    "dataset_id": str(task_dataset_entity.dataset_id),
                    "new_dataset_items": [],
                    "deleted_dataset_items": [],
                    "assigned_dataset_items": assigned_items_chunk,
                },
                key=str(task_node.id_).encode(),
                headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
            )
        for item in training_dataset_items:
            item.id_ = DatasetRepo.generate_id()

        new_training_dataset = Dataset(
            items=training_dataset_items,
            purpose=DatasetPurpose.TRAINING,
            label_schema_id=task_label_schema.id_,
            id=DatasetRepo.generate_id(),
        )
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        dataset_repo.save_deep(new_training_dataset)
        return new_training_dataset

    @staticmethod
    @unified_tracing
    def construct_testing_dataset(
        project: Project,
        dataset_storage: DatasetStorage,
        task_node_id: ID,
        create_new_annotations: bool = False,
    ) -> Dataset:
        """
        Construct testing dataset from all annotated data in dataset storage

        :param project: project containing dataset storage
        :param dataset_storage: dataset storage containing data
        :param task_node_id: task node id
        :param create_new_annotations: If true, create a new ID for the annotation and set kind to intermediate
        :return: evaluation dataset from all annotated media in dataset storage
        """
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        all_annotation_scenes = ann_scene_repo.get_all_by_kind(kind=AnnotationSceneKind.ANNOTATION)
        annotation_scenes = [
            annotation_scene for annotation_scene in all_annotation_scenes if len(annotation_scene.annotations) > 0
        ]
        if create_new_annotations:
            for annotation_scene in annotation_scenes:
                annotation_scene.id_ = AnnotationSceneRepo.generate_id()
                annotation_scene.kind = AnnotationSceneKind.INTERMEDIATE

        dataset = DatasetHelpers.construct_dataset_from_annotation_scenes(
            annotation_scenes=annotation_scenes,
            dataset_storage=dataset_storage,
            subset=Subset.TESTING,
        )
        task_nodes = project.tasks
        if (
            task_node_id != task_nodes[1].id_ and len(task_nodes) == 4
        ):  # TODO: CVS-88185 Remove assumption about length of task chain
            dataset = FlowControl.flow_control(
                project=project,
                task_node=task_nodes[2],
                dataset=dataset,
                prev_task_node=task_nodes[1],
            )
        return dataset

    @staticmethod
    @unified_tracing
    def construct_dataset_from_annotation_scenes(
        annotation_scenes: list[AnnotationScene],
        dataset_storage: DatasetStorage,
        subset: Subset,
    ) -> Dataset:
        """
        Construct dataset from list of annotation scenes

        :param annotation_scenes: list of annotation scenes
        :param dataset_storage: dataset storage including annotation scenes
        :param subset: subset to set items in the dataset to
        :return: dataset
        """
        items = []
        for annotation_scene in annotation_scenes:
            item = DatasetHelper.annotation_scene_to_dataset_item(
                annotation_scene=annotation_scene,
                dataset_storage=dataset_storage,
                subset=subset,
            )
            items.append(item)
        return Dataset(id=DatasetRepo.generate_id(), items=items)
