# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module is responsible for implementing helpers for manipulating datasets
"""

import copy
import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.annotation_scene_state import AnnotationSceneState
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.datasets import Dataset, DatasetPurpose
from iai_core_py.entities.label import Label
from iai_core_py.entities.media_2d import Media2D
from iai_core_py.entities.model_template import TaskFamily
from iai_core_py.entities.project import Project
from iai_core_py.entities.shapes import Rectangle
from iai_core_py.entities.subset import Subset
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.repos import AnnotationSceneRepo, DatasetRepo, LabelSchemaRepo
from iai_core_py.repos.base import SessionBasedRepo
from iai_core_py.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core_py.utils.flow_control import FlowControl
from iai_core_py.utils.media_factory import Media2DFactory

from geti_types import ID, MediaIdentifierEntity, ProjectIdentifier

if TYPE_CHECKING:
    from iai_core_py.entities.label_schema import LabelSchema

logger = logging.getLogger(__name__)


class DatasetHelper:
    """
    Implements helpers for dataset creation and manipulation
    """

    @staticmethod
    def create_dataset_from_media_identifiers(
        dataset_storage: DatasetStorage,
        media_identifiers: list[MediaIdentifierEntity],
        dataset_purpose: DatasetPurpose,
        annotation_scene_kind: AnnotationSceneKind = AnnotationSceneKind.INTERMEDIATE,
        subset: Subset = Subset.NONE,
    ) -> Dataset:
        """
        Creates a dataset from the given media identifiers with empty annotations.

        :param media_identifiers: the list of media identifiers to be inferred
        :param dataset_storage: DatasetStorage containing the dataset items and media
        :param dataset_purpose: purpose to set for the created dataset
        :param annotation_scene_kind: for the created annotations, INTERMEDIATE by default
        :param subset: to set for created dataset items, NONE by default
        :return: a dataset created with the media identifiers and empty annotations.
        """
        dataset_items: list[DatasetItem] = []
        for media_identifier in media_identifiers:
            media = Media2DFactory().get_media_for_identifier(
                media_identifier=media_identifier,
                dataset_storage_identifier=dataset_storage.identifier,
            )
            annotation_scene = AnnotationScene(
                kind=annotation_scene_kind,
                media_identifier=media_identifier,
                media_height=media.height,
                media_width=media.width,
                id_=AnnotationSceneRepo.generate_id(),
            )
            dataset_items.append(
                DatasetItem(
                    media=media,
                    annotation_scene=annotation_scene,
                    subset=subset,
                    id_=DatasetRepo.generate_id(),
                )
            )
        dataset = Dataset(
            items=dataset_items,
            purpose=dataset_purpose,
            id=DatasetRepo.generate_id(),
        )
        DatasetRepo(dataset_storage.identifier).save_deep(dataset)
        return dataset

    @staticmethod
    def get_latest_labels_for_task(
        project_identifier: ProjectIdentifier,
        task_node_id: ID,
        include_empty: bool = False,
    ) -> list[Label]:
        """
        Get the labels from the latest label schema of the given task node.

        :param project_identifier: Identifier of the project relative to the label schema
        :param task_node_id: ID of the task linked with the label schema view from which to retrieve the labels
        :param include_empty: bool indicating whether the empty label should be included in the result
        :return: List of Label objects
        """
        label_schema_repo = LabelSchemaRepo(project_identifier)
        latest_schema = label_schema_repo.get_latest_view_by_task(task_node_id=task_node_id)
        return latest_schema.get_labels(include_empty=include_empty)  # type: ignore[return-value]

    @staticmethod
    def annotation_scene_to_dataset_item(
        annotation_scene: AnnotationScene,
        dataset_storage: DatasetStorage,
        subset: Subset = Subset.NONE,
        roi: Annotation | None = None,
        set_ignored_label_ids: bool = True,
        annotation_scene_state: AnnotationSceneState | None = None,
    ) -> DatasetItem:
        """
        Creates a dataset item from an annotation_scene and adds it to the passed subset
        Optionally adds an ROI and ignored labels to the dataset item.

        :param annotation_scene: Annotation scene to create dataset item with
        :param dataset_storage: DatasetStorage containing the annotations
        :param subset: Subset to add to the dataset item
        :param roi: ROI to add to the dataset item
        :param set_ignored_label_ids: If True, set the 'ignored_label_ids' attribute in the
            dataset item.
        :param annotation_scene_state: If provided and 'set_ignored_label_ids=True', then
            this annotation scene state will be used to compute the ignored labels,
            rather than loading the necessary information from the database.
        :return: DatasetItem
        """
        media = Media2DFactory().get_media_for_identifier(
            media_identifier=annotation_scene.media_identifier,
            dataset_storage_identifier=dataset_storage.identifier,
        )
        dataset_item = DatasetItem(
            id_=DatasetRepo.generate_id(), media=media, annotation_scene=annotation_scene, roi=roi, subset=subset
        )
        if set_ignored_label_ids:
            dataset_item.ignored_label_ids = DatasetHelper.compute_dataset_item_ignored_label_ids(
                item=dataset_item,
                dataset_storage=dataset_storage,
                annotation_scene_state=annotation_scene_state,
            )
        return dataset_item

    @staticmethod
    def create_dataset_up_to_task_from_media_identifiers(
        media_identifiers: Sequence[MediaIdentifierEntity],
        task_node: TaskNode,
        project: Project,
        dataset_storage: DatasetStorage,
        dataset_purpose: DatasetPurpose,
        roi: Annotation | None = None,
        save_to_db: bool = False,
    ) -> Dataset:
        """
        Creates dataset up to task node out of the given media identifiers.
        To build the dataset, it examines all the tasks up to the one with the given id.
        Only user-provided annotations belonging to tasks that precede the selected one
        will be used in the process.

        :param media_identifiers: the media_identifiers used for creating the dataset
        :param task_node: the task for which the inference dataset is to be constructed
        :param roi: Optional roi to perform inference on
        :param project: for which to get dataset
        :param dataset_storage: DatasetStorage containing the dataset items
        :param dataset_purpose: for the created dataset
        :param save_to_db: bool indicating if dataset should be saved to the DB
        :return: task inference dataset
        """
        # CVS-77113
        if roi is not None and len(media_identifiers) > 1:
            raise ValueError("Can only pass ROI argument if one media identifier is passed.")
        labels = DatasetHelper._get_labels_up_to_task(project, task_node)

        # Retrieve the user-provided annotations corresponding to the given media IDs
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        user_annotation_scenes = ann_scene_repo.get_latest_annotations_by_kind_and_identifiers(
            media_identifiers=media_identifiers,
            annotation_kind=AnnotationSceneKind.ANNOTATION,
        )

        # Iterate over these annotations
        dataset_items = [
            DatasetHelper._get_dataset_item_with_filtered_annotations(
                dataset_storage=dataset_storage,
                labels=labels,
                media=Media2DFactory().get_media_for_identifier(
                    media_identifier=media_identifier,
                    dataset_storage_identifier=dataset_storage.identifier,
                ),
                roi=roi,
                task_node=task_node,
                annotation_scene=user_annotation_scene,
                annotation_scene_kind=AnnotationSceneKind.TASK_PREDICTION,
            )
            for media_identifier, user_annotation_scene in zip(media_identifiers, user_annotation_scenes)
        ]
        latest_schema = LabelSchemaRepo(project.identifier).get_latest()
        dataset = Dataset(
            purpose=dataset_purpose,
            id=DatasetRepo.generate_id(),
            items=dataset_items,
            label_schema_id=latest_schema.id_,
        )

        dataset = DatasetHelper._apply_flow_control_up_to_task(
            project=project,
            task_node=task_node,
            dataset=dataset,
        )

        # Save the newly created dataset to DB
        if save_to_db:
            dataset_repo = DatasetRepo(dataset_storage.identifier)
            dataset_repo.save_deep(dataset)

        return dataset

    @staticmethod
    def create_dataset_with_filtered_annotations_up_to_task(
        input_dataset: Dataset,
        task_node: TaskNode,
        project: Project,
        dataset_storage: DatasetStorage,
        annotation_scene_kind: AnnotationSceneKind,
        save_to_db: bool,
    ) -> Dataset:
        """
        Create a copy of a dataset including only user annotations up to (but not
        including) a certain task of the chain.

        For example, if the function is called on the 'classification' task of a
        'detection'->'classification' project, then the resulting dataset will contain
        user annotations for the detection task but NOT classification labels.

        Note: this method examines dataset items one by one, filters the annotations and
        eventually makes a copy; it won't apply any flow-control logic on the dataset.

        :param input_dataset: Dataset used as input for filtering; this dataset is not
            modified in-place, a filtered copy is returned instead.
        :param task_node: Annotations relative to this task and subsequent ones are
            filtered out by this method
        :param project: Project containing the task node
        :param dataset_storage: Dataset storage containing the input dataset
        :param annotation_scene_kind: AnnotationSceneKind to assign to the filtered annotations
        :param save_to_db: bool indicating if dataset should be saved to the DB
        :return: Dataset with filtered annotation
        """
        # Find the labels relative to previous tasks
        labels = DatasetHelper._get_labels_up_to_task(project, task_node)

        # Filter-out the labels relative to this task and next ones
        dataset_items_with_filtered_annotations = [
            DatasetHelper._get_dataset_item_with_filtered_annotations(
                dataset_storage=dataset_storage,
                labels=labels,
                media=dataset_item.media,
                roi=dataset_item.roi,
                task_node=task_node,
                annotation_scene=dataset_item.annotation_scene,
                annotation_scene_kind=annotation_scene_kind,
            )
            for dataset_item in input_dataset
        ]

        filtered_dataset = Dataset(
            purpose=input_dataset.purpose,
            id=DatasetRepo.generate_id(),
            items=dataset_items_with_filtered_annotations,
            label_schema_id=input_dataset.label_schema_id,
        )

        # Save the newly created dataset to DB
        if save_to_db:
            dataset_repo = DatasetRepo(dataset_storage.identifier)
            dataset_repo.save_deep(filtered_dataset)

        return filtered_dataset

    @staticmethod
    def compute_dataset_item_ignored_label_ids(
        item: DatasetItem,
        dataset_storage: DatasetStorage,
        project: Project | None = None,
        annotation_scene_ids: Sequence[ID] | None = None,
        annotation_scene_state: AnnotationSceneState | None = None,
    ) -> set[ID]:
        """
        This method sets the `ignored_label_ids` attribute for a dataset item, if the ID
        of the annotation scene belonging to the item is listed in
        `annotation_scene_ids`.

        This method will query the AnnotationSceneStateRepo to retrieve the
        annotation scene state for the dataset item, and from it will determine how
        the `ignored_label_ids` attribute should be set

        :param item: DatasetItem to set the `ignored_label_ids` attribute for, if required
        :param dataset_storage: Dataset storage containing the dataset
        :param project: Project containing the dataset storage
        :param annotation_scene_ids: List of ID's of annotation scenes that need to
            have their labels revisited
        :param annotation_scene_state: AnnotationSceneState relative to the annotation
            scene in the dataset item. If not provided, it will be loaded from repo.
        :returns: Set of labels to be ignored for this dataset item
        """
        scene_id = item.annotation_scene.id_
        if annotation_scene_ids is not None and scene_id not in annotation_scene_ids:
            # item is not affected, move on
            return set()

        if annotation_scene_state is None:
            annotation_scene_state = AnnotationSceneStateHelper.get_annotation_state_for_scene(
                annotation_scene=item.annotation_scene,
                dataset_storage_identifier=dataset_storage.identifier,
                project=project,
            )

        # Find the ids of the labels to ignore
        is_first_task = item.roi is None or Rectangle.is_full_box(item.roi.shape)
        if is_first_task:
            label_ids_to_ignore = annotation_scene_state.labels_to_revisit_full_scene
        else:
            label_ids_to_ignore = set(annotation_scene_state.labels_to_revisit_per_annotation.get(item.roi.id_, []))

        # Convert the ids to actual labels, filtering out labels not present in the item
        label_ids_in_item = item.get_shapes_label_ids(include_ignored=True)
        return {lbl_id for lbl_id in label_ids_to_ignore if lbl_id in label_ids_in_item}

    @staticmethod
    def clone_dataset(
        dataset: Dataset,
        dataset_storage: DatasetStorage,
        save_db: bool = False,
    ) -> Dataset:
        """
        Create an exact clone of a Dataset.

        All the nested entities are copied and a new ID is assigned to the mutable ones
        that are first-class citizens.

        By default, this function does NOT persist the new Dataset to the DB:
        use the flag 'save_db' to control this behavior.

        :param dataset: Dataset to clone
        :param dataset_storage: Dataset storage containing the dataset
        :param save_db: If True, persist the cloned dataset to the database
        :return: cloned Dataset
        """
        new_scenes_ids: set[ID] = set()

        # Clone the Dataset and the nested objects
        new_dataset = copy.deepcopy(dataset)

        # Assign a new ID to the Dataset
        new_dataset.id_ = SessionBasedRepo.generate_id()
        new_dataset.mark_as_volatile()

        # Assign a new ID to the DatasetItem's
        for item in new_dataset:
            item.id_ = SessionBasedRepo.generate_id()
            item.mark_as_volatile()

            # Assign a new ID to the AnnotationScene, if not already done while
            # processing the same scene in a previous dataset item.
            annotation_scene = item.annotation_scene
            if annotation_scene.id_ in new_scenes_ids:
                continue
            annotation_scene.id_ = AnnotationSceneRepo.generate_id()
            annotation_scene.mark_as_volatile()

        if save_db:
            dataset_repo = DatasetRepo(dataset_storage.identifier)
            dataset_repo.save_deep(new_dataset)

        return new_dataset

    @staticmethod
    def get_dataset_item_label_ids(
        item: DatasetItem,
        task_label_ids: list[ID] | None = None,
        is_task_global: bool = False,
        include_empty: bool = False,
    ) -> set[ID]:
        """
        Get the list of label ids within a dataset item which are pertaining to a task if specified and excluding
        ids of empty labels if `include_empty` is ``False``

        If the task is global, we only check in the roi label ids. If the task is local we check
        both for label ids of the roi and label ids for shapes within the roi because the id of an empty label is added
        as global label id for both local and global tasks

        :param item: the dataset item for which to get labels
        :param task_label_ids: Optional, task label ID's to filter by; if not specified, all labels are included
        :param is_task_global: flag determining whether the task is global or not
        :param include_empty: flag determining whether to include ids of empty labels
        :return: list of relevant label ids in dataset item's roi.
        """
        item_label_ids = item.get_roi_label_ids(label_ids=task_label_ids, include_empty=include_empty)

        if task_label_ids is None or not is_task_global:
            item_label_ids |= item.get_shapes_label_ids(label_ids=task_label_ids, include_empty=include_empty)

        return item_label_ids

    @staticmethod
    def _get_labels_up_to_task(project: Project, task_node: TaskNode) -> list[Label]:
        """
        Get all the labels from tasks before the given task
        """
        labels = []
        for task_node_iter in project.get_trainable_task_nodes():
            if task_node_iter == task_node:
                break
            labels += DatasetHelper.get_latest_labels_for_task(
                project_identifier=project.identifier,
                task_node_id=task_node_iter.id_,
                include_empty=True,
            )
        return labels

    @staticmethod
    def _get_dataset_item_with_filtered_annotations(
        dataset_storage: DatasetStorage,
        labels: list[Label],
        media: Media2D,
        roi: Annotation | None,
        task_node: TaskNode,
        annotation_scene: AnnotationScene,
        annotation_scene_kind: AnnotationSceneKind,
    ) -> DatasetItem:
        """
        Create a dataset item containing only user annotations of previous tasks in the
        task chain

        :param dataset_storage: DatasetStorage where the item belongs
        :param labels: List of Label belonging to tasks before the provided tasks in the
            task chain
        :param media: Media2D of the dataset item
        :param roi: Annotation describing the ROI of the dataset item
        :param task_node: TaskNode for which the inference will be done
        :param annotation_scene: AnnotationScene of the media containing all labels
        :return dataset_item: DatasetItem containing only user annotations for task
            before the provided task
        """
        labels_to_keep_ids = [label.id_ for label in labels]

        # Filter the annotations
        filtered_annotations = DatasetHelper._filter_scene_annotations_by_labels(
            annotation_scene=annotation_scene, label_ids_to_keep=labels_to_keep_ids
        )

        # Filter the ROI
        filtered_roi: Annotation | None = None
        if roi is not None:
            filtered_roi = DatasetHelper._filter_annotation_by_labels(
                annotation=roi,
                label_ids_to_keep=labels_to_keep_ids,
            )
        # Build a new annotation scene with filtered annotations
        filtered_ann_scene = AnnotationScene(
            kind=annotation_scene_kind,
            media_identifier=media.media_identifier,
            media_height=media.height,
            media_width=media.width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id=annotation_scene.last_annotator_id,
            annotations=filtered_annotations,
            invalid_task_ids=annotation_scene.invalid_for_task_ids,
            task_id=task_node.id_,
        )

        return DatasetHelper.annotation_scene_to_dataset_item(
            annotation_scene=filtered_ann_scene,
            roi=filtered_roi,
            dataset_storage=dataset_storage,
        )

    @staticmethod
    def _apply_flow_control_up_to_task(
        project: Project,
        task_node: TaskNode,
        dataset: Dataset,
    ) -> Dataset:
        """
        Apply all flow control appearing before given task node to dataset

        :param dataset: dataset on which to perform flow control
        :param project: Project of the dataset
        :param task_node: TaskNode after flow control operation
        :return output_dataset: Dataset with flow control applied
        """
        prev_task_node: TaskNode | None = None
        label_schema: LabelSchema | None = None
        label_schema_repo = LabelSchemaRepo(project.identifier)
        for task_node_iter in project.tasks:
            if task_node_iter == task_node:
                break
            if task_node_iter.task_properties.task_family is TaskFamily.FLOW_CONTROL:
                if prev_task_node is not None:
                    label_schema = label_schema_repo.get_latest_view_by_task(task_node_id=prev_task_node.id_)
                dataset = FlowControl.flow_control(
                    project=project,
                    task_node=task_node_iter,
                    prev_task_node=prev_task_node,
                    dataset=dataset,
                    label_schema=label_schema,
                )
            prev_task_node = task_node_iter

        return dataset

    @staticmethod
    def _filter_scene_annotations_by_labels(
        annotation_scene: AnnotationScene, label_ids_to_keep: Sequence[ID]
    ) -> list[Annotation]:
        """
        Scan the annotations within an annotation scene and return a copy of them
        after filtering out the labels that are not specified in the input list.

        :param annotation_scene: Annotation scene containing the annotations to filter
        :param label_ids_to_keep: IDs of the labels to keep
        :return: filtered list of Annotation
        """
        filtered_annotations: list[Annotation] = []

        for raw_annotation in annotation_scene.annotations:
            filtered_annotation = DatasetHelper._filter_annotation_by_labels(
                annotation=raw_annotation, label_ids_to_keep=label_ids_to_keep
            )
            if filtered_annotation is not None:
                filtered_annotations.append(filtered_annotation)

        return filtered_annotations

    @staticmethod
    def _filter_annotation_by_labels(annotation: Annotation, label_ids_to_keep: Sequence[ID]) -> Annotation | None:
        """
        Given an Annotation, create a copy of it preserving only the labels with the
        given IDs. If all labels were discarded, then None is returned.
        :param annotation: Annotation to filter
        :param label_ids_to_keep: IDs of the labels to preserve
        :return: Annotation with filtered labels, or None if all labels would be removed
        """
        filtered_annotation_labels = [
            label for label in annotation.get_labels(include_empty=True) if label.id_ in label_ids_to_keep
        ]

        if not filtered_annotation_labels:
            return None

        # Keep original annotation id to ensure UI can match new predictions with existing
        # annotations
        return Annotation(shape=annotation.shape, labels=filtered_annotation_labels, id_=annotation.id_)
