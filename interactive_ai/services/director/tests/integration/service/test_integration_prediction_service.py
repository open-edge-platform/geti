# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import copy
from unittest.mock import patch

from entities.prediction_type import PredictionType
from entities.video_prediction_properties import VideoPredictionProperties
from managers.annotation_manager import AnnotationManager
from service.prediction_service import PredictionService

from geti_types import VideoFrameIdentifier
from sc_sdk.entities.annotation import AnnotationSceneKind
from sc_sdk.repos import AnnotationSceneRepo


class TestPredictionService:
    def test_get_video_predictions_latest(
        self,
        fxt_db_project_service,
        fxt_video_entity,
        fxt_annotation_scene_prediction,
    ) -> None:
        # Arrange
        project = fxt_db_project_service.create_empty_project()
        dataset_storage = project.get_training_dataset_storage()
        dummy_start_frame = 1
        dummy_end_frame = 50
        dummy_frameskip = 3
        dummy_frames = (10, 20, 30)
        dummy_predictions = []
        for i in dummy_frames:
            prediction = copy.deepcopy(fxt_annotation_scene_prediction)
            prediction.media_identifier = VideoFrameIdentifier(video_id=fxt_video_entity.id_, frame_index=i)
            prediction.id_ = AnnotationSceneRepo.generate_id()
            dummy_predictions.append(prediction)

        dummy_video_pagination_properties = VideoPredictionProperties(
            total_count=3,
            start_frame=10,
            end_frame=30,
            total_requested_count=3,
            requested_start_frame=1,
            requested_end_frame=50,
        )

        # Act
        with (
            patch.object(
                AnnotationManager,
                "get_filtered_frame_annotation_scenes",
                return_value=(dummy_predictions, len(dummy_predictions)),
            ) as mock_get_filtered_frame_indices,
        ):
            result = PredictionService.get_video_predictions(
                project=project,
                dataset_storage=dataset_storage,
                video=fxt_video_entity,
                prediction_type=PredictionType.LATEST,
                start_frame=dummy_start_frame,
                end_frame=dummy_end_frame,
                frameskip=dummy_frameskip,
            )
            output, video_pagination_properties = result

        # Assert
        mock_get_filtered_frame_indices.assert_called_once_with(
            dataset_storage_identifier=dataset_storage.identifier,
            video_id=fxt_video_entity.id_,
            annotation_kind=AnnotationSceneKind.PREDICTION,
            start_frame=dummy_start_frame,
            end_frame=dummy_end_frame,
            frameskip=dummy_frameskip,
            limit=500,
            task_id=None,
            model_ids=None,
        )
        assert len(output) == len(dummy_frames)
        assert output == dummy_predictions
        assert video_pagination_properties == dummy_video_pagination_properties
