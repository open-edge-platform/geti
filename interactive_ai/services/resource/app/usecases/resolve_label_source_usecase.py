# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging

from geti_telemetry_tools import unified_tracing
from geti_types import ID, DatasetStorageIdentifier
from sc_sdk.entities.annotation import AnnotationScene, AnnotationSceneKind, NullAnnotationScene
from sc_sdk.entities.scored_label import LabelSource
from sc_sdk.repos import AnnotationSceneRepo

logger = logging.getLogger(__name__)


class ResolveLabelSourceUseCase:
    @staticmethod
    @unified_tracing
    def resolve_label_source_for_annotations(
        annotation_scene: AnnotationScene,
        dataset_storage_identifier: DatasetStorageIdentifier,
        user_id: ID,
    ) -> None:
        """
        Resolve label sources for annotations in annotation scene using previous user
        annotation or model prediction.

        First tries to resolve the label sources of the annotation scene using previous
        annotation scene (user annotation or model prediction). If that fails, and
        previous annotation scene was a model prediction, then tries again using
        previous user created annotation scene.

        :param annotation_scene: the new or updated AnnotationScene object
        :param dataset_storage_identifier: Identifier of the dataset storage
            containing the annotations
        :param user_id: ID of the user who created or updated the annotation.
        """

        annotation_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)

        # Compare with latest user annotation or model prediction for media
        previous_annotation_scene = annotation_scene_repo.get_latest_annotation_by_kind_and_identifier(
            media_identifier=annotation_scene.media_identifier,
            annotation_kind=[
                AnnotationSceneKind.ANNOTATION,
                AnnotationSceneKind.PREDICTION,
                AnnotationSceneKind.TASK_PREDICTION,
            ],
        )
        did_any_shape_match = ResolveLabelSourceUseCase._update_label_sources(
            new_annotation_scene=annotation_scene,
            previous_annotation_scene=previous_annotation_scene,
            user_id=user_id,
        )

        # If model prediction does not match at all, try comparing with previous user
        # annotation
        if not did_any_shape_match and previous_annotation_scene.kind in {
            AnnotationSceneKind.PREDICTION,
            AnnotationSceneKind.TASK_PREDICTION,
        }:
            previous_annotation_scene = annotation_scene_repo.get_latest_annotation_by_kind_and_identifier(
                media_identifier=annotation_scene.media_identifier,
                annotation_kind=[AnnotationSceneKind.ANNOTATION],
            )
            if not isinstance(previous_annotation_scene, NullAnnotationScene):
                ResolveLabelSourceUseCase._update_label_sources(
                    new_annotation_scene=annotation_scene,
                    previous_annotation_scene=previous_annotation_scene,
                    user_id=user_id,
                )

    @staticmethod
    def _update_label_sources(
        new_annotation_scene: AnnotationScene,
        previous_annotation_scene: AnnotationScene,
        user_id: ID,
    ) -> bool:
        """
        Update empty label sources of new annotation scene.

        If an annotation from the new annotation scene matches with an annotation from
        the previous annotation scene, copy the label source from the previous
        annotation. If the previous annotation scene was a prediction, add the current
        user to the label source. For new annotations or for newly added labels, the
        current user is added as the label source.

        If the previous annotation scene is the NullAnnotationScene, all labels of all
        annotations will get the current user added to the label source.

        :param new_annotation_scene: new AnnotationScene without label sources
        :param previous_annotation_scene: previous AnnotationScene with label sources
        :param user_id: ID of the user who created or updated the annotation.
        """
        did_any_shape_match = False

        previous_annotation_ids = {annotation.id_ for annotation in previous_annotation_scene.annotations}

        for new_annotation in new_annotation_scene.annotations:
            new_labels = new_annotation.get_labels(include_empty=True)
            if new_annotation.id_ in previous_annotation_ids:
                # annotation already existed, compare labels within this annotation
                did_any_shape_match = True
                previous_annotation = next(
                    previous_annotation
                    for previous_annotation in previous_annotation_scene.annotations
                    if new_annotation.id_ == previous_annotation.id_
                )
                previous_labels = previous_annotation.get_labels(include_empty=True)
                previous_label_ids = {previous_label.id_ for previous_label in previous_labels}

                for new_label in new_labels:
                    if new_label.id_ in previous_label_ids:
                        # label already existed, copy label source from previous
                        # annotation
                        previous_label = next(
                            previous_label for previous_label in previous_labels if previous_label.id_ == new_label.id_
                        )
                        previous_label_source = previous_label.label_source
                        new_label.label_source = LabelSource(
                            user_id=previous_label_source.user_id,
                            model_id=previous_label_source.model_id,
                            model_storage_id=previous_label_source.model_storage_id,
                        )
                        if not previous_label.label_source.user_id:
                            # previous label was predicted by model, add user to label
                            # source as the one who accepted
                            new_label.label_source.user_id = user_id
                    else:
                        # new label added by current user
                        new_label.label_source.user_id = user_id
            else:
                # new annotation created by current user
                for new_label in new_labels:
                    new_label.label_source.user_id = user_id

        return did_any_shape_match
