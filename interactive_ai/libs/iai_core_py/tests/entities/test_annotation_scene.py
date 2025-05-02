# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from copy import deepcopy

from iai_core_py.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.scored_label import LabelSource, ScoredLabel


class TestAnnotationScene:
    def test_get_model_ids(
        self,
        fxt_rectangle_annotation,
        fxt_label,
        fxt_ote_id,
    ) -> None:
        # Arrange
        dummy_user_id = "test_user"
        model_id_1 = fxt_ote_id(123)
        model_id_2 = fxt_ote_id(124)
        model_id_3 = fxt_ote_id(125)
        scored_label_1 = ScoredLabel(
            label_id=fxt_label.id_, is_empty=fxt_label.is_empty, label_source=LabelSource(model_id=model_id_1)
        )
        scored_label_2 = ScoredLabel(
            label_id=fxt_label.id_, is_empty=fxt_label.is_empty, label_source=LabelSource(model_id=model_id_2)
        )
        scored_label_3 = ScoredLabel(
            label_id=fxt_label.id_,
            is_empty=fxt_label.is_empty,
            label_source=LabelSource(user_id=dummy_user_id, model_id=model_id_3),
        )
        annotation_1 = fxt_rectangle_annotation
        annotation_2 = deepcopy(annotation_1)
        annotation_3 = deepcopy(annotation_2)
        annotation_by_user = deepcopy(fxt_rectangle_annotation)
        annotation_1.set_labels([scored_label_1])
        annotation_2.set_labels([scored_label_2])
        annotation_3.set_labels([])
        annotation_by_user.set_labels([scored_label_3])
        annotations = [annotation_1, annotation_2, annotation_3, annotation_by_user]
        dummy_width, dummy_height = 100, 100

        # Act
        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=fxt_ote_id(0),
            media_height=dummy_height,
            media_width=dummy_width,
            id_=fxt_ote_id(1),
            annotations=annotations,
        )

        # Assert
        model_ids_no_user_annotations = annotation_scene.get_model_ids(include_user_annotations=False)
        assert model_ids_no_user_annotations == {model_id_1, model_id_2}
        model_ids_with_user_annotations = annotation_scene.get_model_ids(include_user_annotations=True)
        assert model_ids_with_user_annotations == {model_id_1, model_id_2, model_id_3}
