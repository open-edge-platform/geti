# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TYPE_CHECKING
from unittest.mock import ANY, call, patch

import pytest

from sc_sdk.algorithms.crop.task import CropTask
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.entities.subset import Subset
from sc_sdk.repos import AnnotationSceneRepo, DatasetRepo, LabelSchemaRepo
from sc_sdk.services import ModelService
from sc_sdk.utils.dataset_helper import DatasetHelper
from sc_sdk.utils.media_factory import Media2DFactory

if TYPE_CHECKING:
    from sc_sdk.entities.label_schema import LabelSchema
    from sc_sdk.entities.project import Project


@pytest.mark.ScSdkComponent
class TestDatasetHelper:
    def test_create_dataset_from_media_identifiers(
        self, fxt_dataset_storage, fxt_image_identifier, fxt_image_entity, fxt_mongo_id
    ) -> None:
        expected_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.INTERMEDIATE,
            media_identifier=fxt_image_identifier,
            media_height=fxt_image_entity.height,
            media_width=fxt_image_entity.width,
            id_=fxt_mongo_id(0),
        )
        expected_dataset_item = DatasetItem(
            id_=fxt_mongo_id(1), media=fxt_image_entity, annotation_scene=expected_annotation_scene, subset=Subset.NONE
        )
        expected_dataset = Dataset(
            items=[expected_dataset_item],
            purpose=DatasetPurpose.INFERENCE,
            id=fxt_mongo_id(1),
        )
        with (
            patch.object(Media2DFactory, "get_media_for_identifier", return_value=fxt_image_entity) as mock_get_media,
            patch.object(
                AnnotationSceneRepo, "generate_id", return_value=fxt_mongo_id(0)
            ) as mock_generate_annotation_id,
            patch.object(DatasetRepo, "generate_id", return_value=fxt_mongo_id(1)) as mock_generate_item_id,
            patch.object(DatasetRepo, "save_deep", return_value=None) as mock_save_dataset,
        ):
            result = DatasetHelper.create_dataset_from_media_identifiers(
                dataset_storage=fxt_dataset_storage,
                media_identifiers=[fxt_image_identifier],
                dataset_purpose=DatasetPurpose.INFERENCE,
            )

            assert result == expected_dataset
            mock_get_media.assert_called_once_with(
                media_identifier=fxt_image_identifier,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
            )
            mock_generate_annotation_id.assert_called_once_with()
            mock_generate_item_id.assert_has_calls([call(), call()])
            mock_save_dataset.assert_called_once_with(expected_dataset)

    def test_create_dataset_up_to_task_from_media_identifiers(
        self,
        fxt_segmentation_task,
        fxt_detection_segmentation_chain_project,
        fxt_dataset_storage,
        fxt_image_identifier,
        fxt_label_schema,
        fxt_annotation_scene,
        fxt_mongo_id,
        fxt_image_entity,
        fxt_dataset_item,
        fxt_model_storage_detection,
        fxt_label,
    ) -> None:
        expected_dataset_item = fxt_dataset_item()
        expected_dataset = Dataset(
            purpose=DatasetPurpose.TASK_INFERENCE,
            id=fxt_mongo_id(1),
            items=[expected_dataset_item],
            label_schema_id=fxt_label_schema.id_,
        )
        with (
            patch.object(DatasetRepo, "generate_id", return_value=fxt_mongo_id(1)),
            patch.object(
                AnnotationSceneRepo, "generate_id", return_value=fxt_mongo_id(0)
            ) as mock_generate_annotation_id,
            patch.object(
                AnnotationSceneRepo,
                "get_latest_annotations_by_kind_and_identifiers",
                return_value=[fxt_annotation_scene],
            ) as mock_get_annotations,
            patch.object(Media2DFactory, "get_media_for_identifier", return_value=fxt_image_entity) as mock_get_media,
            patch.object(
                LabelSchemaRepo,
                "get_latest_view_by_task",
                return_value=fxt_label_schema,
            ) as mock_get_task_label_schema,
            patch.object(LabelSchemaRepo, "get_latest", return_value=fxt_label_schema),
            patch.object(
                DatasetHelper,
                "annotation_scene_to_dataset_item",
                return_value=expected_dataset_item,
            ) as mock_scene_to_item,
            patch.object(DatasetRepo, "save_deep", return_value=None) as mock_save_dataset,
            patch.object(
                ModelService,
                "get_active_model_storage",
                return_value=fxt_model_storage_detection,
            ),
            patch.object(CropTask, "_get_labels_from_previous_task", return_value=[fxt_label]),
        ):
            result = DatasetHelper.create_dataset_up_to_task_from_media_identifiers(
                media_identifiers=[fxt_image_identifier],
                task_node=fxt_segmentation_task,
                project=fxt_detection_segmentation_chain_project,
                dataset_storage=fxt_dataset_storage,
                dataset_purpose=DatasetPurpose.TASK_INFERENCE,
                save_to_db=True,
            )

            assert result == expected_dataset
            mock_generate_annotation_id.assert_called_once_with()
            mock_get_annotations.assert_called_once_with(
                media_identifiers=[fxt_image_identifier],
                annotation_kind=AnnotationSceneKind.ANNOTATION,
            )
            mock_get_media.assert_called_once_with(
                media_identifier=fxt_image_identifier,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
            )
            mock_scene_to_item.assert_called_once_with(
                annotation_scene=ANY,
                roi=None,
                dataset_storage=fxt_dataset_storage,
            )
            mock_save_dataset.assert_called_once_with(expected_dataset)
            task_node_iter = fxt_detection_segmentation_chain_project.get_trainable_task_nodes()[0]
            mock_get_task_label_schema.assert_has_calls(
                [
                    call(
                        task_node_id=task_node_iter.id_,
                    ),
                    call(
                        task_node_id=task_node_iter.id_,
                    ),
                ]
            )

    @pytest.mark.parametrize("task_index", [0, 1], ids=["Up to the first task (det)", "Up to the second task (seg)"])
    def test_create_dataset_with_filtered_annotations_up_to_task(
        self,
        task_index,
        fxt_detection_segmentation_chain_project,
        fxt_detection_label_schema,
        fxt_segmentation_label_schema,
        fxt_model_storage_detection,
        fxt_ote_id,
        fxt_image_entity,
    ) -> None:
        """Test the method on a regular (not cropped) dataset"""

        project: Project = fxt_detection_segmentation_chain_project
        det_task_node = project.get_trainable_task_nodes()[0]
        seg_task_node = project.get_trainable_task_nodes()[1]
        dataset_storage = project.get_training_dataset_storage()
        det_label_schema: LabelSchema = fxt_detection_label_schema
        seg_label_schema: LabelSchema = fxt_segmentation_label_schema
        det_labels = det_label_schema.get_labels(include_empty=True)
        seg_labels = seg_label_schema.get_labels(include_empty=True)
        det_empty = next(lbl for lbl in det_labels if lbl.is_empty)
        det_non_empty = next(lbl for lbl in det_labels if not lbl.is_empty)
        seg_empty = next(lbl for lbl in seg_labels if lbl.is_empty)
        seg_non_empty = next(lbl for lbl in seg_labels if not lbl.is_empty)
        this_task_node = det_task_node if task_index == 0 else seg_task_node

        # Two annotation scenes: first one has two fully-annotated bboxes; second one
        # has a partially annotated bbox.
        bbox1 = Rectangle(0.3, 0.4, 0.5, 0.6)
        bbox2 = Rectangle(0.1, 0.2, 0.3, 0.4)
        ann_1_1 = Annotation(
            shape=bbox1, labels=[ScoredLabel(label_id=det_non_empty.id_), ScoredLabel(label_id=seg_non_empty.id_)]
        )
        ann_1_2 = Annotation(
            shape=bbox2,
            labels=[ScoredLabel(label_id=det_non_empty.id_), ScoredLabel(label_id=seg_empty.id_, is_empty=True)],
        )
        ann_2_1 = Annotation(shape=bbox1, labels=[ScoredLabel(label_id=det_empty.id_, is_empty=True)])
        ann_scene_1 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_image_entity.media_identifier,
            media_height=fxt_image_entity.height,
            media_width=fxt_image_entity.width,
            id_=fxt_ote_id(1),
            annotations=[ann_1_1, ann_1_2],
        )
        ann_scene_2 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_image_entity.media_identifier,
            media_height=fxt_image_entity.height,
            media_width=fxt_image_entity.width,
            id_=fxt_ote_id(2),
            annotations=[ann_2_1],
        )
        # The dataset is relative to the first task, not cropped (roi=None)
        dataset_item_1 = DatasetItem(
            media=fxt_image_entity,
            annotation_scene=ann_scene_1,
            roi=None,
            id_=fxt_ote_id(11),
        )
        dataset_item_2 = DatasetItem(
            media=fxt_image_entity,
            annotation_scene=ann_scene_2,
            roi=None,
            id_=fxt_ote_id(12),
        )
        in_dataset = Dataset(items=[dataset_item_1, dataset_item_2], id=fxt_ote_id(100))

        with (
            patch.object(
                LabelSchemaRepo,
                "get_latest_view_by_task",
                new=lambda _self, task_node_id: (
                    det_label_schema if task_node_id == det_task_node.id_ else seg_label_schema
                ),
            ),
            patch.object(
                LabelSchemaRepo,
                "get_by_id",
                new=lambda _self, label_schema_id: (
                    det_label_schema if label_schema_id == det_label_schema.id_ else seg_label_schema
                ),
            ),
            patch.object(
                ModelService,
                "get_active_model_storage",
                return_value=fxt_model_storage_detection,
            ),
            patch.object(DatasetRepo, "save_deep", return_value=None) as mock_save_dataset,
        ):
            out_dataset = DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
                input_dataset=in_dataset,
                task_node=this_task_node,
                project=project,
                dataset_storage=dataset_storage,
                annotation_scene_kind=AnnotationSceneKind.TASK_PREDICTION,
                save_to_db=True,
            )

        mock_save_dataset.assert_called()
        # Expect as many output items as in the input dataset
        assert len(out_dataset) == 2
        # Expect the ROI to be full-image rectangles as in the original dataset
        assert Rectangle.is_full_box(out_dataset[0].roi.shape)
        assert Rectangle.is_full_box(out_dataset[1].roi.shape)
        assert not out_dataset[0].get_roi_label_ids()
        assert not out_dataset[1].get_roi_label_ids()
        if task_index == 0:  # detection
            # Expect no labels (all filtered out)
            assert not out_dataset[0].get_annotations()
            assert not out_dataset[1].get_annotations()
        else:  # segmentation
            # Expect only labels relative to the detection task
            annotations_1 = out_dataset[0].get_annotations()
            assert len(annotations_1) == 2
            assert not out_dataset[1].get_annotations()
            assert annotations_1[0].get_labels()[0].label_id == det_non_empty.id_
            assert annotations_1[1].get_labels()[0].label_id == det_non_empty.id_

    def test_create_dataset_with_filtered_annotations_up_to_task_on_cropped_task(
        self,
        fxt_detection_segmentation_chain_project,
        fxt_detection_label_schema,
        fxt_segmentation_label_schema,
        fxt_model_storage_detection,
        fxt_ote_id,
        fxt_image_entity,
    ) -> None:
        """Test the method on a cropped dataset"""

        project: Project = fxt_detection_segmentation_chain_project
        det_task_node = project.get_trainable_task_nodes()[0]
        seg_task_node = project.get_trainable_task_nodes()[1]
        dataset_storage = project.get_training_dataset_storage()
        det_label_schema: LabelSchema = fxt_detection_label_schema
        seg_label_schema: LabelSchema = fxt_segmentation_label_schema
        det_labels = det_label_schema.get_labels(include_empty=True)
        seg_labels = seg_label_schema.get_labels(include_empty=True)
        next(lbl for lbl in det_labels if lbl.is_empty)
        det_non_empty = next(lbl for lbl in det_labels if not lbl.is_empty)
        seg_empty = next(lbl for lbl in seg_labels if lbl.is_empty)
        seg_non_empty = next(lbl for lbl in seg_labels if not lbl.is_empty)
        this_task_node = seg_task_node

        # Two annotation scenes: first one has two fully-annotated bboxes; second one
        # has a partially annotated bbox.
        bbox1 = Rectangle(0.3, 0.4, 0.5, 0.6)
        bbox2 = Rectangle(0.1, 0.2, 0.3, 0.4)
        ann_1_1 = Annotation(
            shape=bbox1, labels=[ScoredLabel(label_id=det_non_empty.id_), ScoredLabel(label_id=seg_non_empty.id_)]
        )
        ann_1_2 = Annotation(
            shape=bbox2,
            labels=[ScoredLabel(label_id=det_non_empty.id_), ScoredLabel(label_id=seg_empty.id_, is_empty=True)],
        )
        ann_2_1 = Annotation(shape=bbox1, labels=[ScoredLabel(label_id=det_non_empty.id_)])
        ann_scene_1 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_image_entity.media_identifier,
            media_height=fxt_image_entity.height,
            media_width=fxt_image_entity.width,
            id_=fxt_ote_id(1),
            annotations=[ann_1_1, ann_1_2],
        )
        ann_scene_2 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_image_entity.media_identifier,
            media_height=fxt_image_entity.height,
            media_width=fxt_image_entity.width,
            id_=fxt_ote_id(2),
            annotations=[ann_2_1],
        )
        # The dataset is relative to the second task (cropped) thus contains 3 items
        # in total, one for each bbox
        dataset_item_1_1 = DatasetItem(
            media=fxt_image_entity,
            annotation_scene=ann_scene_1,
            roi=ann_1_1,
            id_=fxt_ote_id(11),
        )
        dataset_item_1_2 = DatasetItem(
            id_=fxt_ote_id(11), media=fxt_image_entity, annotation_scene=ann_scene_1, roi=ann_1_2
        )
        dataset_item_2_1 = DatasetItem(
            media=fxt_image_entity,
            annotation_scene=ann_scene_2,
            roi=ann_2_1,
            id_=fxt_ote_id(12),
        )
        in_dataset = Dataset(items=[dataset_item_1_1, dataset_item_1_2, dataset_item_2_1], id=fxt_ote_id(100))

        with (
            patch.object(
                LabelSchemaRepo,
                "get_latest_view_by_task",
                new=lambda _self, task_node_id: (
                    det_label_schema if task_node_id == det_task_node.id_ else seg_label_schema
                ),
            ),
            patch.object(
                LabelSchemaRepo,
                "get_by_id",
                new=lambda _self, label_schema_id: (
                    det_label_schema if label_schema_id == det_label_schema.id_ else seg_label_schema
                ),
            ),
            patch.object(
                ModelService,
                "get_active_model_storage",
                return_value=fxt_model_storage_detection,
            ),
            patch.object(DatasetRepo, "save_deep", return_value=None) as mock_save_dataset,
        ):
            out_dataset = DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
                input_dataset=in_dataset,
                task_node=this_task_node,
                project=project,
                dataset_storage=dataset_storage,
                annotation_scene_kind=AnnotationSceneKind.TASK_PREDICTION,
                save_to_db=True,
            )

        mock_save_dataset.assert_called()
        # Expect as many output items as in the input dataset
        assert len(out_dataset) == len(in_dataset)
        # Expect the ROIs to be bounding boxes as the annotations
        assert out_dataset[0].roi.shape == ann_1_1.shape
        assert out_dataset[1].roi.shape == ann_1_2.shape
        assert out_dataset[2].roi.shape == ann_2_1.shape
        for out_item in out_dataset:
            assert out_item.roi.get_labels()[0].label_id == det_non_empty.id_
            # Expect only labels relative to the first task (detection)
            for ann in out_item.get_annotations():
                assert {scored_lbl.label_id for scored_lbl in ann.get_labels()} == {det_non_empty.id_}

    def test_annotation_scene_to_dataset_item(
        self,
        fxt_image_entity,
        fxt_annotation_scene,
        fxt_annotation_scene_state,
        fxt_rectangle_annotation,
        fxt_mongo_id,
        fxt_dataset_storage,
        fxt_label,
    ) -> None:
        expected_dataset_item = DatasetItem(
            media=fxt_image_entity,
            annotation_scene=fxt_annotation_scene,
            subset=Subset.TESTING,
            roi=fxt_rectangle_annotation,
            id_=fxt_mongo_id(0),
            ignored_label_ids=[fxt_label],
        )
        with (
            patch.object(DatasetRepo, "generate_id", return_value=fxt_mongo_id(0)) as mock_generate_id,
            patch.object(Media2DFactory, "get_media_for_identifier", return_value=fxt_image_entity) as mock_get_media,
            patch.object(
                DatasetHelper,
                "compute_dataset_item_ignored_label_ids",
                return_value=[fxt_label],
            ),
        ):
            result = DatasetHelper.annotation_scene_to_dataset_item(
                annotation_scene=fxt_annotation_scene,
                dataset_storage=fxt_dataset_storage,
                subset=Subset.TESTING,
                roi=fxt_rectangle_annotation,
                set_ignored_label_ids=True,
                annotation_scene_state=fxt_annotation_scene_state,
            )

            mock_generate_id.assert_called_once_with()
            mock_get_media.assert_called_once_with(
                media_identifier=fxt_annotation_scene.media_identifier,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
            )

            assert result == expected_dataset_item

    @pytest.mark.parametrize("save_db", [False, True])
    def test_clone_dataset(self, save_db, fxt_dataset, fxt_mongo_id, fxt_dataset_storage) -> None:
        original_dataset = fxt_dataset
        with patch.object(DatasetRepo, "save_deep", return_value=None) as mock_save_dataset:
            cloned_dataset = DatasetHelper.clone_dataset(
                dataset=fxt_dataset, dataset_storage=fxt_dataset_storage, save_db=save_db
            )

            if save_db:
                mock_save_dataset.assert_called_once_with(cloned_dataset)
            else:
                mock_save_dataset.assert_not_called()
            assert len(cloned_dataset) == len(original_dataset)
            assert {di.id_ for di in cloned_dataset}.intersection({di.id_ for di in original_dataset}) == set()
