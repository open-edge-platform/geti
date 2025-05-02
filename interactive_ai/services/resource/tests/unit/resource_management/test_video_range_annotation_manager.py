# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import TYPE_CHECKING
from unittest.mock import patch

from managers.annotation_manager import AnnotationManager
from resource_management import VideoRangeAnnotationManager
from service.label_schema_service import LabelSchemaService

from geti_types import ID, DatasetStorageIdentifier
from iai_core.entities.annotation import AnnotationSceneKind
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.scored_label import LabelSource, ScoredLabel
from iai_core.entities.shapes import Rectangle
from iai_core.repos import LabelSchemaRepo, VideoAnnotationRangeRepo
from iai_core.utils.identifier_factory import IdentifierFactory

if TYPE_CHECKING:
    from iai_core.entities.annotation import AnnotationScene


@patch(
    "iai_core.repos.annotation_scene_repo.AnnotationSceneRepo.__init__",
    return_value=None,
)
class TestVideoRangeAnnotationManager:
    def test_create_video_annotations(
        self,
        fxt_annotation_scene_state,
        fxt_project,
        fxt_dataset_storage,
        fxt_video_entity,
        fxt_label,
        fxt_video_frame_identifier,
    ):
        dummy_label_schema = LabelSchema(id_=ID("dummy_id"))

        with (
            patch.object(
                AnnotationManager,
                "save_annotations",
                return_value=((None, fxt_annotation_scene_state, None),),
            ) as mock_save_annotations,
            patch.object(
                IdentifierFactory,
                "generate_frame_identifiers_for_video",
                return_value=[fxt_video_frame_identifier],
            ),
            patch.object(
                LabelSchemaRepo,
                "get_latest",
                return_value=dummy_label_schema,
            ),
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_task",
                return_value=dummy_label_schema,
            ),
        ):
            state_per_task = VideoRangeAnnotationManager.create_global_annotations_for_video(
                project=fxt_project,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video=fxt_video_entity,
                labels=[fxt_label],
                user_id=ID("dummy_user"),
            )

            saved_scene: AnnotationScene = mock_save_annotations.mock_calls[0].kwargs["annotation_scenes"][0]
            dataset_storage_identifier = DatasetStorageIdentifier(
                workspace_id=fxt_project.workspace_id,
                project_id=fxt_project.id_,
                dataset_storage_id=fxt_dataset_storage.id_,
            )
            ann_range_repo = VideoAnnotationRangeRepo(dataset_storage_identifier)
            ann_range = ann_range_repo.get_latest_by_video_id(fxt_video_entity.id_)

            assert state_per_task == fxt_annotation_scene_state.state_per_task
            assert len(ann_range.range_labels) == 1
            assert ann_range.range_labels[0].start_frame == 0
            assert ann_range.range_labels[0].end_frame == fxt_video_entity.total_frames
            assert ann_range.range_labels[0].label_ids == (fxt_label.id_,)
            assert len(saved_scene.annotations) == 1
            assert saved_scene.annotations[0].get_labels() == [
                ScoredLabel(
                    label_id=fxt_label.id_,
                    is_empty=fxt_label.is_empty,
                    probability=1.0,
                    label_source=LabelSource(user_id=ID("dummy_user")),
                )
            ]
            assert Rectangle.is_full_box(saved_scene.annotations[0].shape)
            assert saved_scene.media_identifier == fxt_video_frame_identifier
            assert saved_scene.kind == AnnotationSceneKind.ANNOTATION
            mock_save_annotations.assert_called_once_with(
                annotation_scenes=[saved_scene],
                project=fxt_project,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                label_schema=dummy_label_schema,
                label_schema_by_task={fxt_project.task_ids[1]: dummy_label_schema},
                calculate_task_to_revisit=False,
            )
