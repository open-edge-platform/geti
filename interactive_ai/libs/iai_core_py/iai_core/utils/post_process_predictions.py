# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the post process prediction utilities
"""

import logging

import cv2
import numpy as np

from iai_core.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelSchema, LabelSchemaView
from iai_core.entities.model import Model, NullModel
from iai_core.entities.scored_label import LabelSource, ScoredLabel
from iai_core.entities.shapes import Point, Polygon
from iai_core.entities.task_node import NullTaskNode, TaskNode
from iai_core.repos import AnnotationSceneRepo, DatasetRepo
from iai_core.utils.constants import MAX_POLYGON_POINTS

from geti_types import ID

logger = logging.getLogger(__name__)


class PostProcessPredictionsUtils:
    """
    Use case to post process predicted labels to respect the label hierarchy and add a
    label source.
    """

    @staticmethod
    def post_process_prediction_dataset(  # noqa: C901, PLR0913
        dataset_storage: DatasetStorage,
        dataset: Dataset,
        model: Model = NullModel(),
        task_node: TaskNode = NullTaskNode(),
        dataset_purpose: DatasetPurpose | None = None,
        annotation_scene_kind: AnnotationSceneKind | None = None,
        reload_from_db: bool = False,
        save_to_db: bool = True,
    ) -> Dataset:
        """
        Post-process predictions to reload in-memory dataset and ensure consistent labelling

        - Reload the dataset and the annotation scenes from the database (if not ephemeral)
        - Update the dataset purpose
        - Add parent labels and remove mutually exclusive labels from predictions (if task
            node is given and trainable)
        - Update annotation scene kind
        - Add empty label to dataset item, if no labels are predicted for the ROI (if task
            node is given and trainable)
        - Save dataset and all annotations to database.

        :param dataset_storage: The dataset storage of the dataset
        :param dataset: The dataset containing the new predictions
        :param model: The model that generated the new predictions. Only relevant if
            task_node is provided.
        :param task_node: The task for which the new predictions were made. Optional, if
            not provided, only the annotation scene kind is updated.
        :param dataset_purpose: New purpose to set in the dataset. If not provided, the
            purpose of the dataset will not be changed.
        :param annotation_scene_kind: The new annotation scene kind of the annotations.
            If unspecified, it will be deduced from the dataset purpose.
        :param reload_from_db: bool to indicating if dataset should be reloaded from the DB
        :param save_to_db: bool indicating if dataset should be saved to the DB
        """

        label_schema: LabelSchema = model.get_label_schema()
        task_labels = label_schema.get_labels(include_empty=True)
        if isinstance(label_schema, LabelSchemaView):
            label_schema = label_schema.parent_schema

        # Get latest version of dataset from db
        dataset_repo: DatasetRepo = DatasetRepo(dataset_storage.identifier)
        if reload_from_db:
            dataset = dataset_repo.get_by_id(dataset.id_)

        # Update the dataset purpose
        if dataset_purpose is not None:
            dataset.purpose = dataset_purpose

        # In a task chain several dataset items may reference the same annotation scene,
        # but with a different ROI. To avoid resolving the same annotation scene, keep a
        # dictionary of resolved annotation scenes.
        resolved_annotation_scenes: dict[ID, AnnotationScene] = {}

        # Determine the AnnotationSceneKind to apply to all the scenes in the dataset.
        if annotation_scene_kind is None:
            annotation_scene_kind = PostProcessPredictionsUtils._get_annotation_kind_from_purpose(
                purpose=dataset.purpose
            )

        annotation_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        for dataset_item in dataset:
            annotation_scene_id = dataset_item.annotation_scene.id_
            if annotation_scene_id not in resolved_annotation_scenes:
                if reload_from_db:
                    new_annotation_scene = annotation_scene_repo.get_by_id(annotation_scene_id)
                else:
                    new_annotation_scene = dataset_item.annotation_scene

                # Update annotation scene kind and task id
                new_annotation_scene.kind = annotation_scene_kind
                if annotation_scene_kind == AnnotationSceneKind.TASK_PREDICTION and task_node.id_ != ID():
                    new_annotation_scene.task_id = task_node.id_

                # Filter out non-tasks labels and add the model as the label source.
                if task_node.task_properties.is_trainable:
                    PostProcessPredictionsUtils._post_process_labels(
                        annotation_scene=new_annotation_scene,
                        model=model,
                    )

                resolved_annotation_scenes[annotation_scene_id] = new_annotation_scene

            # Checks if empty label needs to be added
            if task_node.task_properties.is_trainable:
                PostProcessPredictionsUtils._resolve_empty_label_for_task(
                    dataset_item=dataset_item,
                    model=model,
                    task_labels=task_labels,
                    task_is_global=task_node.task_properties.is_global,
                )

        # Save dataset to db, including the dataset items and annotation scenes
        if save_to_db:
            dataset_repo.save_deep(instance=dataset)
        return dataset

    @staticmethod
    def _get_annotation_kind_from_purpose(
        purpose: DatasetPurpose,
    ) -> AnnotationSceneKind:
        """
        Return annotation scene kind based on the purpose of a dataset.
        """
        look_up_dict = {
            DatasetPurpose.INFERENCE: AnnotationSceneKind.PREDICTION,
            DatasetPurpose.EVALUATION: AnnotationSceneKind.EVALUATION,
            DatasetPurpose.TASK_INFERENCE: AnnotationSceneKind.TASK_PREDICTION,
            DatasetPurpose.TEMPORARY_DATASET: AnnotationSceneKind.INTERMEDIATE,
        }
        try:
            return look_up_dict[purpose]
        except KeyError:
            logger.warning(
                "Could not determine annotation kind from dataset purpose '%s'. Defaulting to PREDICTION.",
                purpose.name,
            )
            return AnnotationSceneKind.PREDICTION

    @staticmethod
    def _post_process_labels(
        annotation_scene: AnnotationScene,
        model: Model,
    ) -> None:
        """
        Adds the model as label source and filter out label that do not belong to the task.

        :param annotation_scene: AnnotationScene that will be processed
        :param model: Model that predicted the latest labels
        for ephemeral inference.
        """
        for annotation in annotation_scene.annotations:
            annotation_labels = annotation.get_labels()

            # Check for empty label sources and add model as the source
            for label in annotation_labels:
                if label.label_source == LabelSource():
                    label.label_source = LabelSource(model_id=model.id_, model_storage_id=model.model_storage.id_)

            # If the current model is the source for all labels, it must have predicted the
            # shape as well. If the predicted shape is a polygon, we optimize it to avoid
            # unnecessary large number of points.
            if isinstance(annotation.shape, Polygon) and all(
                model.id_ == label.label_source.model_id for label in annotation_labels
            ):
                annotation.shape = PostProcessPredictionsUtils._optimize_polygon_curve(
                    shape=annotation.shape,
                    media_width=annotation_scene.media_width,
                    media_height=annotation_scene.media_height,
                )
            annotation.set_labels(annotation_labels)

    @staticmethod
    def _resolve_empty_label_for_task(
        dataset_item: DatasetItem,
        model: Model,
        task_labels: list[Label],
        task_is_global: bool,
    ) -> bool:
        """
        Add empty label if no other label exists for the task

        :param dataset_item: The dataset item
        :param model: Model that predicted the latest labels
        :param task_labels: The labels of the task
        :param task_is_global: Whether the task is global or not
        :return: True if an empty label is added, otherwise it returns
            the state of annotation_scene_updated
        """
        task_label_ids = {label.id_ for label in task_labels}
        label_ids = dataset_item.get_roi_label_ids(label_ids=task_label_ids, include_empty=False)
        if not task_is_global:
            # gathers also all the local shapes' labels
            # if it is a local task (e.g., segmentation, detection)
            label_ids |= dataset_item.get_shapes_label_ids(label_ids=task_label_ids, include_empty=False)

        if len(label_ids) == 0:
            # adds a label if there is no label attached to the dataset item
            empty_label = next((label for label in task_labels if label.is_empty), None)
            if empty_label is not None:  # only add if empty_label exists
                # todo: CVS-62227
                empty_scored_label = ScoredLabel(
                    label_id=empty_label.id_,
                    is_empty=True,
                    probability=1.0,
                    label_source=LabelSource(model_id=model.id_, model_storage_id=model.model_storage.id_),
                )
                dataset_item.append_labels([empty_scored_label])
                return True
        return False

    @staticmethod
    def _optimize_polygon_curve(shape: Polygon, media_width: int, media_height: int) -> Polygon:
        """
        Optimizes the polygon's points to not exceed MAX_POLYGON_POINTS.
        The function will de-normalize the polygon to compute the optimization, this is
        because the epsilon value cannot be trivially normalized. If the optimization
        leaves the polygon with 2 or less points, return the original shape instead of the
        optimized shape.

        :param shape: The Polygon to optimize
        :param media_width: Width of the media in pixels
        :param media_height: Height of the media in pixels
        :return: The optimized Polygon
        """
        epsilon = 0.5
        polygon_np = np.array(
            [[p.x * media_width, p.y * media_height] for p in shape.points],
            dtype=np.float32,
        )
        polygon_np_cv2 = cv2.approxPolyDP(polygon_np, epsilon, closed=True)
        while len(polygon_np_cv2) >= MAX_POLYGON_POINTS:
            epsilon += 0.1
            polygon_np_cv2 = cv2.approxPolyDP(polygon_np, epsilon, closed=True)
        polygon_points = [
            Point(x=float(p[0][0] / media_width), y=float(p[0][1]) / media_height) for p in polygon_np_cv2
        ]
        return Polygon(polygon_points) if len(polygon_points) > 2 else shape
