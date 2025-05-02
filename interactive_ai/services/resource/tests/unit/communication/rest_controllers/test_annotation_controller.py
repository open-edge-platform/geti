# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import cast
from unittest.mock import ANY, MagicMock, call, patch

import pytest
from testfixtures import compare

from communication.exceptions import AnnotationsNotFoundException
from communication.rest_controllers.annotation_controller import LATEST, AnnotationRESTController
from communication.rest_data_validator import AnnotationRestValidator
from communication.rest_views.video_annotation_range_rest_views import VideoAnnotationRangeRESTViews
from managers.annotation_manager import AnnotationManager
from managers.project_manager import ProjectManager
from service.label_schema_service import LabelSchemaService

from geti_types import ID, DatasetStorageIdentifier, ImageIdentifier, VideoFrameIdentifier
from iai_core_py.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.label_schema import LabelSchema, NullLabelSchema
from iai_core_py.entities.video import Video
from iai_core_py.entities.video_annotation_range import NullVideoAnnotationRange, VideoAnnotationRange
from iai_core_py.repos import AnnotationSceneRepo, LabelSchemaRepo, VideoAnnotationRangeRepo, VideoRepo


class TestAnnotationRESTController:
    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_annotation_scene, lazyfxt_annotation_scene_rest, label_only",
        [
            ("fxt_annotation_scene", "fxt_annotation_scene_rest_response", False),
            (
                "fxt_annotation_scene_label_only",
                "fxt_annotation_scene_rest_label_only",
                True,
            ),
        ],
    )
    # fmt: on
    def test_get_annotation(
        self,
        lazyfxt_annotation_scene,
        lazyfxt_annotation_scene_rest,
        label_only,
        fxt_mongo_id,
        fxt_project,
        fxt_annotation_scene_state,
        request,
    ):
        image_id = fxt_mongo_id(1)
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_project.training_dataset_storage_id,
        )
        media_identifier = ImageIdentifier(image_id=image_id)
        annotation_scene = request.getfixturevalue(lazyfxt_annotation_scene)
        annotation_scene_rest = request.getfixturevalue(lazyfxt_annotation_scene_rest)

        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                AnnotationManager,
                "get_latest_annotation_scene_for_media",
                return_value=annotation_scene,
            ) as mock_get_anno,
            patch.object(
                AnnotationManager,
                "get_annotation_state_information_for_scene",
                return_value=(fxt_annotation_scene_state, []),
            ) as mock_get_anno_state,
            patch.object(LabelSchemaRepo, "get_latest", return_value=NullLabelSchema()),
        ):
            result = AnnotationRESTController().get_annotation(
                dataset_storage_identifier=dataset_storage_identifier,
                annotation_id=ID("latest"),
                media_identifier=media_identifier,
                label_only=label_only,
            )

            mock_get_project.assert_called_once_with(project_id=fxt_project.id_)
            mock_get_anno.assert_called_once_with(
                dataset_storage_identifier=dataset_storage_identifier,
                media_identifier=media_identifier,
            )
            mock_get_anno_state.assert_called_once_with(
                dataset_storage_identifier=dataset_storage_identifier,
                annotation_scene=annotation_scene,
                project=fxt_project,
            )
            compare(result, annotation_scene_rest, ignore_eq=True)

    def test_get_annotation_not_found(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_annotation_scene_no_annotations,
    ):
        image_id = fxt_mongo_id(1)
        media_identifier = ImageIdentifier(image_id=image_id)

        with (
            pytest.raises(AnnotationsNotFoundException),
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                AnnotationManager,
                "get_latest_annotation_scene_for_media",
                return_value=fxt_annotation_scene_no_annotations,
            ) as mock_get_anno,
        ):
            AnnotationRESTController().get_annotation(
                dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
                annotation_id=ID("latest"),
                media_identifier=media_identifier,
                label_only=True,
            )

            mock_get_project.assert_called_once_with(project_id=fxt_project.id_)
            mock_get_anno.assert_called_once_with(
                dataset_storage=fxt_project.get_training_dataset_storage(),
                media_identifier=media_identifier,
            )

    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_ann_scenes_list, lazyfxt_ann_scenes_list_rest, lazyfxt_ann_scene_states_list, label_only",
        [
            ("fxt_ann_scenes_list", "fxt_ann_scenes_list_rest",
             "fxt_ann_scene_states_list", False),
            ("fxt_ann_scenes_list_label_only", "fxt_ann_scenes_list_rest_label_only",
             "fxt_ann_scene_states_list_label_only", True),
        ],
        ids=["Return full annotations", "Return labels only"],
    )
    # fmt: on
    def test_get_video_frame_annotations(
        self,
        fxt_mongo_id,
        fxt_project,
        lazyfxt_ann_scenes_list,
        lazyfxt_ann_scenes_list_rest,
        lazyfxt_ann_scene_states_list,
        label_only,
        request,
    ):
        dataset_storage = fxt_project.get_training_dataset_storage()
        video_id = fxt_mongo_id(3)
        annotation_scenes_list = request.getfixturevalue(lazyfxt_ann_scenes_list)
        annotation_scene_states_list = request.getfixturevalue(lazyfxt_ann_scene_states_list)
        annotation_scenes_list_rest = request.getfixturevalue(lazyfxt_ann_scenes_list_rest)
        start_frame = 1
        end_frame = 6
        frameskip = 2

        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                AnnotationManager,
                "get_filtered_frame_annotation_scenes",
                return_value=(annotation_scenes_list, len(annotation_scenes_list)),
            ) as mock_get_frames,
            patch.object(
                AnnotationManager,
                "get_annotation_state_information_for_scenes",
                return_value=(annotation_scene_states_list, [[], []]),
            ) as mock_get_anno_states,
            patch.object(
                LabelSchemaRepo,
                "get_latest",
                return_value=LabelSchema(id_=fxt_mongo_id(4)),
            ),
        ):
            result = AnnotationRESTController.get_video_frame_annotations(
                project_id=dataset_storage.project_id,
                dataset_storage_id=dataset_storage.id_,
                video_id=ID(video_id),
                annotation_id=ID(LATEST),
                label_only=label_only,
                start_frame=start_frame,
                end_frame=end_frame,
                frameskip=frameskip,
            )

            mock_get_project.assert_called_once_with(project_id=dataset_storage.project_id)
            mock_get_frames.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier,
                video_id=video_id,
                start_frame=start_frame,
                end_frame=end_frame,
                frameskip=frameskip,
                limit=500,
            )
            mock_get_anno_states.assert_called_once_with(
                dataset_storage=fxt_project.get_training_dataset_storage(),
                annotation_scenes=annotation_scenes_list,
                project=fxt_project,
            )
            compare(
                result["video_annotations"],
                annotation_scenes_list_rest["video_annotations"],
                ignore_eq=True,
            )
            count = len(annotation_scenes_list)
            page_properties = {
                "total_count": count,
                "start_frame": None,
                "end_frame": None,
                "total_requested_count": count,
                "requested_start_frame": start_frame,
                "requested_end_frame": end_frame,
            }
            compare(result["video_annotation_properties"], page_properties, ignore_eq=True)

    def test_get_video_frame_annotations_empty(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_annotation_scene_no_annotations,
    ) -> None:
        project_id = fxt_mongo_id(2)
        video_id = fxt_mongo_id(3)
        annotated_frame_indices = (2, 4)
        start_frame = 1
        end_frame = 6
        frameskip = 2

        with (
            pytest.raises(AnnotationsNotFoundException),
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                AnnotationManager,
                "get_filtered_frame_annotation_scenes",
                return_value=([], 0),
            ) as mock_get_anno,
            patch.object(
                LabelSchemaRepo,
                "get_latest",
                return_value=LabelSchema(id_=fxt_mongo_id(4)),
            ),
        ):
            AnnotationRESTController().get_video_frame_annotations(
                project_id=ID(project_id),
                dataset_storage_id=fxt_project.training_dataset_storage_id,
                video_id=ID(video_id),
                annotation_id=ID(LATEST),
                label_only=True,
                start_frame=start_frame,
                end_frame=end_frame,
                frameskip=frameskip,
            )

            mock_get_project.assert_called_once_with(project_id=project_id)
            mock_get_anno.assert_called_once_with(
                dataset_storage=fxt_project.get_training_dataset_storage(),
                media_id=video_id,
                frames_indices=annotated_frame_indices,
                start_frame=start_frame,
                end_frame=end_frame,
                frameskip=frameskip,
                limit=500,
            )

    def test_get_video_range_annotation(self, fxt_dataset_storage_identifier, fxt_mongo_id) -> None:
        dummy_var_rest = {"key": "value"}
        video_id = fxt_mongo_id(11)
        dummy_video_ann_range = VideoAnnotationRange(id_=fxt_mongo_id(12), video_id=video_id, range_labels=[])
        with (
            patch.object(
                VideoAnnotationRangeRepo, "get_latest_by_video_id", return_value=dummy_video_ann_range
            ) as mock_get_latest_var,
            patch.object(
                VideoAnnotationRangeRESTViews, "video_annotation_range_to_rest", return_value=dummy_var_rest
            ) as mock_var_to_rest
        ):
            out_var_rest = AnnotationRESTController.get_video_range_annotation(
                dataset_storage_identifier=fxt_dataset_storage_identifier, video_id=video_id
            )

        mock_get_latest_var.assert_called_once_with(video_id=video_id)
        mock_var_to_rest.assert_called_once_with(video_annotation_range=dummy_video_ann_range)
        assert out_var_rest == dummy_var_rest

    def test_make_video_range_annotation(
        self,
        fxt_project_with_classification_task,
        fxt_classification_label_schema,
        fxt_dataset_storage_identifier,
        fxt_mongo_id,
    ) -> None:
        project, label_schema = fxt_project_with_classification_task, fxt_classification_label_schema
        video = MagicMock(spec=Video)
        dummy_video_ann_range = VideoAnnotationRange(id_=fxt_mongo_id(12), video_id=video.id_, range_labels=[])
        dummy_video_ann_range_rest = {"range_labels": [{"start_frame": 1, "end_frame": 10, "label_ids": []}]}
        with (
            patch(
                "communication.rest_controllers.annotation_controller.check_free_space_for_operation"
            ) as mock_check_free_space,
            patch.object(ProjectManager, "get_project_by_id", return_value=project),
            patch.object(LabelSchemaRepo, "get_latest", return_value=label_schema),
            patch.object(VideoRepo, "get_by_id", return_value=video),
            patch.object(VideoAnnotationRangeRepo, "get_latest_by_video_id", return_value=NullVideoAnnotationRange()),
            patch.object(VideoAnnotationRangeRepo, "save") as mock_save_var,
            patch.object(AnnotationRestValidator, "validate_video_annotation_range") as mock_validate_var,
            patch.object(
                VideoAnnotationRangeRESTViews, "video_annotation_range_from_rest", return_value=dummy_video_ann_range
            ) as mock_var_from_rest,
            patch.object(
                VideoAnnotationRangeRESTViews, "video_annotation_range_to_rest", return_value=dummy_video_ann_range_rest
            ) as mock_var_to_rest,
            patch.object(AnnotationRESTController, "create_annotations_for_video_range") as mock_create_annotations,
        ):
            out_var_rest = AnnotationRESTController.make_video_range_annotation(
                video_annotation_range_data=dummy_video_ann_range_rest,
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video_id=video.id_,
                user_id=ID("dummy_user"),
                skip_frame=3,
            )

        mock_check_free_space.assert_called_once()
        mock_validate_var.assert_called_once_with(
            video_annotation_range_rest=dummy_video_ann_range_rest,
            label_schema=label_schema,
            video_total_frames=video.total_frames,
        )
        mock_var_from_rest.assert_called_once_with(
            video_annotation_range_data=dummy_video_ann_range_rest, video_id=video.id_
        )
        mock_save_var.assert_called_once_with(dummy_video_ann_range)
        mock_create_annotations.assert_called_once_with(
            new_video_annotation_range=dummy_video_ann_range,
            old_video_annotation_range=NullVideoAnnotationRange(),
            video=video,
            project=project,
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            label_schema=label_schema,
            user_id=ID("dummy_user"),
            skip_frame=3,
        )
        mock_var_to_rest.assert_called_once_with(video_annotation_range=dummy_video_ann_range)
        assert out_var_rest == dummy_video_ann_range_rest

    def test_create_annotations_for_video_range(
        self,
        fxt_project,
        fxt_classification_label_schema,
        fxt_dataset_storage_identifier,
        fxt_mongo_id,
    ) -> None:
        label_0, label_1 = fxt_classification_label_schema.get_labels(include_empty=True)[:2]
        new_video_ann_range = MagicMock(spec=VideoAnnotationRange)
        old_video_ann_range = MagicMock(spec=VideoAnnotationRange)
        video = MagicMock(spec=Video)
        video.id_ = fxt_mongo_id(11)
        video.total_frames = 10
        with (
            patch.object(new_video_ann_range, "get_labels_at_frame_index", return_value={label_0.id_}),
            patch.object(old_video_ann_range, "get_labels_at_frame_index", return_value={label_1.id_}),
            patch.object(AnnotationManager, "save_annotations") as mock_save_annotations,
            patch.object(
                AnnotationSceneRepo, "get_video_frame_annotations_by_video_id", return_value=([], 0)
            ) as mock_get_frame_anns,
            patch.object(
                LabelSchemaService, "get_latest_label_schema_for_task", return_value=fxt_classification_label_schema
            ),
        ):
            AnnotationRESTController.create_annotations_for_video_range(
                new_video_annotation_range=new_video_ann_range,
                old_video_annotation_range=old_video_ann_range,
                video=video,
                project=fxt_project,
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                label_schema=fxt_classification_label_schema,
                user_id=ID("dummy_user"),
                skip_frame=4,
            )

        mock_get_frame_anns.assert_has_calls(
            [
                call(
                    video_id=video.id_,
                    start_frame=1,
                    end_frame=3,
                    annotation_kind=AnnotationSceneKind.ANNOTATION,
                ),
                call(
                    video_id=video.id_,
                    start_frame=5,
                    end_frame=7,
                    annotation_kind=AnnotationSceneKind.ANNOTATION,
                ),
                call(
                    video_id=video.id_,
                    start_frame=9,
                    end_frame=9,
                    annotation_kind=AnnotationSceneKind.ANNOTATION,
                ),
            ]
        )
        mock_save_annotations.assert_called_once_with(
            annotation_scenes=ANY,
            project=fxt_project,
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            label_schema=fxt_classification_label_schema,
            label_schema_by_task=ANY,
            calculate_task_to_revisit=False,
        )
        saved_scenes: list[AnnotationScene] = mock_save_annotations.mock_calls[0].kwargs["annotation_scenes"]
        assert len(saved_scenes) == 3  # annotations should be created for frames [0, 4, 8]
        assert all(ann_scene.media_identifier.media_id == video.id_ for ann_scene in saved_scenes)
        saved_frame_indices = {
            cast("VideoFrameIdentifier", ann_scene.media_identifier).frame_index for ann_scene in saved_scenes
        }
        assert saved_frame_indices == {0, 4, 8}
