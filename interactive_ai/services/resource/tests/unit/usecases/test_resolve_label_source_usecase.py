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
from typing import TYPE_CHECKING
from unittest.mock import patch

from usecases.resolve_label_source_usecase import ResolveLabelSourceUseCase

from geti_types import ID
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind, NullAnnotationScene
from sc_sdk.entities.scored_label import LabelSource, ScoredLabel
from sc_sdk.repos import AnnotationSceneRepo

if TYPE_CHECKING:
    from sc_sdk.entities.label import Label


@patch(
    "sc_sdk.repos.annotation_scene_repo.AnnotationSceneRepo.__init__",
    return_value=None,
)
class TestResolveLabelSourceUseCase:
    def test_update_label_sources_some_matches(
        self,
        patched_repo,
        fxt_mongo_id,
        fxt_media_identifier,
        fxt_classification_label_schema_factory,
        fxt_rectangle_shape,
    ):
        # Arrange
        user_1 = ID("user_1")
        user_2 = ID("user_2")
        annotation_id = fxt_mongo_id(0)
        model_id = fxt_mongo_id(1)
        model_storage_id = fxt_mongo_id(2)

        cls_label_schema = fxt_classification_label_schema_factory(num_labels=3)
        cls_label_0: Label = cls_label_schema.get_labels(False)[0]
        cls_label_1: Label = cls_label_schema.get_labels(False)[1]
        cls_label_2: Label = cls_label_schema.get_labels(False)[2]

        scored_label_0 = ScoredLabel(label_id=cls_label_0.id_)
        scored_label_1 = ScoredLabel(label_id=cls_label_1.id_)
        scored_label_2 = ScoredLabel(label_id=cls_label_2.id_)
        prev_scored_label_0 = ScoredLabel(label_id=cls_label_0.id_, label_source=LabelSource(user_id=user_1))
        prev_scored_label_1 = ScoredLabel(
            label_id=cls_label_1.id_,
            probability=0.8,
            label_source=LabelSource(model_id=model_id, model_storage_id=model_storage_id),
        )

        new_annotation = Annotation(
            shape=fxt_rectangle_shape, labels=[scored_label_0, scored_label_1, scored_label_2], id_=annotation_id
        )
        prev_annotation = Annotation(
            shape=fxt_rectangle_shape, labels=[prev_scored_label_0, prev_scored_label_1], id_=annotation_id
        )

        new_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_media_identifier,
            media_height=400,
            media_width=800,
            id_=fxt_mongo_id(3),
            annotations=[new_annotation],
        )
        prev_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_media_identifier,
            media_height=400,
            media_width=800,
            id_=fxt_mongo_id(3),
            annotations=[prev_annotation],
        )

        # Act
        did_any_shape_match = ResolveLabelSourceUseCase._update_label_sources(
            new_annotation_scene=new_annotation_scene,
            previous_annotation_scene=prev_annotation_scene,
            user_id=user_2,
        )

        # Assert
        assert did_any_shape_match

        labels = new_annotation_scene.annotations[0].get_labels()
        assert labels[0].label_source == LabelSource(user_id=user_1)
        assert labels[1].label_source == LabelSource(
            user_id=user_2, model_id=model_id, model_storage_id=model_storage_id
        )
        assert labels[2].label_source == LabelSource(user_id=user_2)

    def test_update_label_sources_no_matches(
        self,
        patched_repo,
        fxt_mongo_id,
        fxt_media_identifier,
        fxt_classification_label,
        fxt_rectangle_shape,
    ):
        # Arrange
        scored_label = ScoredLabel(label_id=fxt_classification_label.id_)

        # Annotations are compared by id
        new_annotation = Annotation(shape=fxt_rectangle_shape, labels=[scored_label], id_=fxt_mongo_id(1))
        prev_annotation = Annotation(shape=fxt_rectangle_shape, labels=[scored_label], id_=fxt_mongo_id(2))

        new_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_media_identifier,
            media_height=400,
            media_width=800,
            id_=fxt_mongo_id(3),
            annotations=[new_annotation],
        )
        prev_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_media_identifier,
            media_height=400,
            media_width=800,
            id_=fxt_mongo_id(3),
            annotations=[prev_annotation],
        )

        # Act
        did_any_shape_match = ResolveLabelSourceUseCase._update_label_sources(
            new_annotation_scene=new_annotation_scene,
            previous_annotation_scene=prev_annotation_scene,
            user_id=ID("dummy_user"),
        )

        # Assert
        assert not did_any_shape_match

    def test_update_label_sources_all_matches(self, patched_repo, fxt_annotation_scene):
        # Act
        did_any_shape_match = ResolveLabelSourceUseCase._update_label_sources(
            new_annotation_scene=fxt_annotation_scene,
            previous_annotation_scene=fxt_annotation_scene,
            user_id=ID("dummy_user"),
        )

        # Assert
        assert did_any_shape_match

    def test_update_label_sources_new_annotation(
        self,
        patched_repo,
        fxt_mongo_id,
        fxt_media_identifier,
        fxt_classification_label,
        fxt_rectangle_shape,
    ):
        # Arrange
        scored_label = ScoredLabel(label_id=fxt_classification_label.id_)

        new_annotation = Annotation(shape=fxt_rectangle_shape, labels=[scored_label], id_=fxt_mongo_id(1))

        new_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=fxt_media_identifier,
            media_height=400,
            media_width=800,
            id_=fxt_mongo_id(3),
            annotations=[new_annotation],
        )

        # Act
        did_any_shape_match = ResolveLabelSourceUseCase._update_label_sources(
            new_annotation_scene=new_annotation_scene,
            previous_annotation_scene=NullAnnotationScene(),
            user_id=ID("dummy_user"),
        )

        # Assert
        labels = new_annotation_scene.annotations[0].get_labels(include_empty=True)
        assert len(labels) == 1
        assert labels[0].label_source == LabelSource(user_id=ID("dummy_user"))
        assert not did_any_shape_match

    def test_resolve_label_source_normal(self, patched_repo, fxt_annotation_scene, fxt_dataset_storage):
        # Arrange
        fxt_annotation_scene.kind = AnnotationSceneKind.ANNOTATION

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_latest_annotation_by_kind_and_identifier",
                return_value=fxt_annotation_scene,
            ) as mocked_repo,
            patch.object(ResolveLabelSourceUseCase, "_update_label_sources", return_value=True) as mocked_compare,
        ):
            ResolveLabelSourceUseCase.resolve_label_source_for_annotations(
                annotation_scene=fxt_annotation_scene,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                user_id=ID("dummy_user"),
            )

        # Assert
        mocked_repo.assert_called_once()
        mocked_compare.assert_called_once()

    def test_resolve_label_source_no_match(self, patched_repo, fxt_annotation_scene, fxt_dataset_storage):
        # Arrange
        fxt_annotation_scene.kind = AnnotationSceneKind.PREDICTION

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_latest_annotation_by_kind_and_identifier",
                return_value=fxt_annotation_scene,
            ) as mocked_repo,
            patch.object(
                ResolveLabelSourceUseCase,
                "_update_label_sources",
                return_value=False,
            ) as mocked_compare,
        ):
            ResolveLabelSourceUseCase.resolve_label_source_for_annotations(
                annotation_scene=fxt_annotation_scene,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                user_id=ID("dummy_user"),
            )

        # Assert
        assert mocked_repo.call_count == 2
        assert mocked_compare.call_count == 2

    def test_resolve_label_source_all_match_annotation(self, patched_repo, fxt_annotation_scene, fxt_dataset_storage):
        # Arrange
        fxt_annotation_scene.kind = AnnotationSceneKind.ANNOTATION

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_latest_annotation_by_kind_and_identifier",
                return_value=fxt_annotation_scene,
            ) as mocked_repo,
            patch.object(ResolveLabelSourceUseCase, "_update_label_sources", return_value=True) as mocked_compare,
        ):
            ResolveLabelSourceUseCase.resolve_label_source_for_annotations(
                annotation_scene=fxt_annotation_scene,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                user_id=ID("dummy_user"),
            )

        # Assert
        assert mocked_repo.call_count == 1
        assert mocked_compare.call_count == 1

    def test_resolve_label_source_all_match_prediction(self, patched_repo, fxt_annotation_scene, fxt_dataset_storage):
        # Arrange
        fxt_annotation_scene.kind = AnnotationSceneKind.PREDICTION

        # Act
        with (
            patch.object(
                AnnotationSceneRepo,
                "get_latest_annotation_by_kind_and_identifier",
                return_value=fxt_annotation_scene,
            ) as mocked_repo,
            patch.object(ResolveLabelSourceUseCase, "_update_label_sources", return_value=True) as mocked_compare,
        ):
            ResolveLabelSourceUseCase.resolve_label_source_for_annotations(
                annotation_scene=fxt_annotation_scene,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                user_id=ID("dummy_user"),
            )

        # Assert
        assert mocked_repo.call_count == 1
        assert mocked_compare.call_count == 1
