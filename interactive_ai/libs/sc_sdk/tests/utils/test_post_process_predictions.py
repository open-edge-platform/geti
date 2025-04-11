# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
import math
from unittest.mock import patch

import pytest
from shapely.geometry import Polygon as ShapelyPolgon

from sc_sdk.entities.annotation import Annotation, AnnotationSceneKind
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.model import Model
from sc_sdk.entities.project import Project
from sc_sdk.entities.scored_label import LabelSource, ScoredLabel
from sc_sdk.entities.shapes import Point, Polygon
from sc_sdk.repos import AnnotationSceneRepo, DatasetRepo, LabelSchemaRepo
from sc_sdk.utils.post_process_predictions import PostProcessPredictionsUtils


@pytest.mark.ScSdkComponent
class TestPostProcessPredictions:
    def test_post_process_predictions_with_annotations(
        self, project_with_data, fxt_single_random_classification_row, fxt_model
    ) -> None:
        """
        This test checks if the LabelSource is correctly added to predictions with
        annotations.
        """
        # Arrange
        project: Project = project_with_data.project
        task_node = project.get_trainable_task_nodes()[0]
        task_label_schema = LabelSchemaRepo(project.identifier).get_latest_view_by_task(task_node_id=task_node.id_)
        task_labels = task_label_schema.get_labels(include_empty=False)

        dataset_item_1 = fxt_single_random_classification_row(project=project, labels=task_labels)
        dataset_item_2 = fxt_single_random_classification_row(project=project, labels=task_labels)

        annotation = dataset_item_2.annotation_scene.annotations[0]
        labels = annotation.get_labels()
        labels[0].label_source = LabelSource(user_id="user_1")
        annotation.set_labels(labels)

        dataset = Dataset(items=[dataset_item_1, dataset_item_2], id=DatasetRepo.generate_id())

        # Assert LabelSource is empty
        annotations_1 = dataset_item_1.annotation_scene.annotations
        labels = annotations_1[0].get_labels(include_empty=True)
        assert labels[0].label_source == LabelSource()

        with (
            patch.object(DatasetRepo, "save", return_value=None),
            patch.object(AnnotationSceneRepo, "save", return_value=None),
            patch.object(Model, "get_label_schema", return_value=task_label_schema) as patched_get_label_schema,
        ):
            # Act
            dataset_storage = project.get_training_dataset_storage()
            PostProcessPredictionsUtils.post_process_prediction_dataset(
                dataset_storage=dataset_storage,
                dataset=dataset,
                model=fxt_model,
                task_node=task_node,
                dataset_purpose=DatasetPurpose.TASK_INFERENCE,
                reload_from_db=False,
                save_to_db=False,
            )

        # Assert
        assert dataset.purpose == DatasetPurpose.TASK_INFERENCE

        annotation_scene_1 = dataset_item_1.annotation_scene
        assert annotation_scene_1.kind == AnnotationSceneKind.TASK_PREDICTION
        assert annotation_scene_1.task_id == task_node.id_
        annotations_1 = annotation_scene_1.annotations
        labels = annotations_1[0].get_labels(include_empty=True)
        assert labels[0].label_source == LabelSource(
            model_id=fxt_model.id_, model_storage_id=fxt_model.model_storage.id_
        )

        annotation_scene_2 = dataset_item_2.annotation_scene
        assert annotation_scene_2.kind == AnnotationSceneKind.TASK_PREDICTION
        assert annotation_scene_2.task_id == task_node.id_
        annotations_2 = annotation_scene_2.annotations
        labels = annotations_2[0].get_labels(include_empty=True)
        assert labels[0].label_source == LabelSource(user_id="user_1")

        patched_get_label_schema.assert_called_once_with()

    def test_process_polygon_annotation_with_over_5000_points(
        self, project_with_data, fxt_single_crate_image_dataset_for_project, fxt_model
    ) -> None:
        """
        This tests if a prediction annotation with more than 5000 points is optimized.
        """
        # Arrange
        project: Project = project_with_data.project
        label_schema_repo = LabelSchemaRepo(project.identifier)
        project_label_schema = label_schema_repo.get_latest()
        labels = project_label_schema.get_labels(include_empty=False)
        # Create annotation with 5001 points
        points = [Point(x=math.sin(2 * math.pi * p / 5001), y=math.cos(2 * math.pi * p / 5001)) for p in range(5001)]
        annotations = [Annotation(Polygon(points), [ScoredLabel(label_id=labels[0].id_, is_empty=labels[0].is_empty)])]
        _, dataset = fxt_single_crate_image_dataset_for_project(project=project, annotations=annotations)
        task_node = project.get_trainable_task_nodes()[0]
        task_label_schema = label_schema_repo.get_latest_view_by_task(task_node_id=task_node.id_)

        # Assert that we have an annotation with 5001 points
        assert len(dataset[0].annotation_scene.annotations[0].shape.points) == 5001
        with (
            patch.object(DatasetRepo, "save", return_value=None),
            patch.object(AnnotationSceneRepo, "save", return_value=None),
            patch.object(Model, "get_label_schema", return_value=task_label_schema) as patched_get_label_schema,
        ):
            # Act
            dataset_storage = project.get_training_dataset_storage()
            PostProcessPredictionsUtils.post_process_prediction_dataset(
                dataset_storage=dataset_storage,
                dataset=dataset,
                model=fxt_model,
                task_node=task_node,
                reload_from_db=False,
                save_to_db=False,
            )
        # Assert that the resolve was successful by checking that the annotation
        # has fewer than 5000 points
        assert len(dataset[0].annotation_scene.annotations[0].shape.points) < 5000
        patched_get_label_schema.assert_called_once_with()

    def test_optimize_polygon(
        self,
    ) -> None:
        """
        Test that a triangle with a small angle is not converted to an invalid polygon.
        """
        # Create triangle with small angle polygon
        polygon = Polygon(points=[Point(0.1, 0.9), Point(0.9, 0.9), Point(0.9, 0.905)])
        media_width = 100
        media_height = 100

        # Optimize polygon
        optimized_polygon = PostProcessPredictionsUtils._optimize_polygon_curve(
            polygon, media_width=media_width, media_height=media_height
        )

        # Check that polygon can still be converted to shapely polygon after optimization
        ShapelyPolgon([(point.x * media_width, point.y * media_height) for point in optimized_polygon.points])
