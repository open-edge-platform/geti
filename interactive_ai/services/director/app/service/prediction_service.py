# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

"""
This module contains the PredictionService class
"""

import logging

from communication.constants import MAX_N_ANNOTATIONS_RETURNED, MAX_N_PREDICTIONS_RETURNED
from communication.exceptions import NoPredictionsFoundException, PredictionNotFoundException
from entities import PredictionType
from entities.video_prediction_properties import VideoPredictionProperties
from managers.annotation_manager import AnnotationManager

from geti_telemetry_tools import unified_tracing
from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, VideoFrameIdentifier
from sc_sdk.entities.annotation import AnnotationScene, AnnotationSceneKind, NullAnnotationScene
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.project import Project
from sc_sdk.entities.video import Video
from sc_sdk.repos import AnnotationSceneRepo

logger = logging.getLogger(__name__)


class PredictionService:
    @staticmethod
    @unified_tracing
    def _get_single_prediction(
        project: Project,
        dataset_storage: DatasetStorage,
        media_identifier: MediaIdentifierEntity,
        prediction_type: PredictionType = PredictionType.ONLINE,
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
    ) -> AnnotationScene:
        """
        Gets the prediction for a media_identifier, depending on the requested result_id

        :param project: Project containing the dataset storage
        :param dataset_storage: Dataset storage containing the media
        :param media_identifier: Media for which to get predictions
        :param prediction_type: PredictionType (latest, auto or online)
            - latest: return the latest prediction from the DB
            - auto: try to get the latest prediction from the DB; if missing, generate
              a new one by means of the inference server
            - online: generate a new prediction by means of the inference server
        :param task_id: if supplied, the prediction will be relative to this task node.
            Note: this parameter is ignored for single-task projects.
        :param model_ids: if supplied, the prediction must be relative to the models
        :param roi_id: if supplied, the prediction will be relative to this ROI
        :return: AnnotationScene corresponding to the prediction; NullAnnotationScene
            if the prediction could not be found or generated.
        """
        # Fetch a previously cached prediction from the DB (auto/latest mode only), if
        # it exists
        if prediction_type in [PredictionType.LATEST, PredictionType.AUTO]:
            ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
            prediction_kind = PredictionService._get_prediction_kind(model_ids, project, task_id)
            prediction = ann_scene_repo.get_latest_annotation_by_kind_and_identifier(
                media_identifier=media_identifier,
                annotation_kind=prediction_kind,
                task_id=task_id,
                model_ids=model_ids,
            )
            if isinstance(prediction, NullAnnotationScene):
                logger.info(
                    "Could not find existing prediction (%s mode) for media %s and task ID `%s`",
                    prediction_type.name,
                    media_identifier,
                    task_id,
                )
            return prediction
        raise ValueError(f"Unknown or unsupported prediction type {prediction_type.name}")

    @staticmethod
    def _get_prediction_kind(model_ids: set[ID] | None, project: Project, task_id: ID | None) -> AnnotationSceneKind:
        """
        Determine the type of the prediction to pull based on the number of trainable
        tasks in the pipeline and the prediction endpoint 'task_id' or 'model_ids'
        parameter value:
         - task-chain with task_id or one model_id specified -> TASK_PREDICTION
         - all other cases -> PREDICTION
        """
        is_task_chain = len(project.get_trainable_task_nodes()) > 1
        is_task_prediction = task_id is not None or (model_ids is not None and len(model_ids) == 1)
        return (
            AnnotationSceneKind.TASK_PREDICTION
            if (is_task_chain and is_task_prediction)
            else AnnotationSceneKind.PREDICTION
        )

    @staticmethod
    @unified_tracing
    def get_video_predictions(  # noqa: PLR0913
        project: Project,
        dataset_storage: DatasetStorage,
        video: Video,
        prediction_type: PredictionType,
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
        start_frame: int | None = None,
        end_frame: int | None = None,
        frameskip: int | None = None,
    ) -> tuple[list[AnnotationScene], VideoPredictionProperties]:
        """
        Get the predictions and the result media for the frames inside a video.

        :param project: The project to get the predictions for
        :param dataset_storage: The dataset storage containing video
        :param video: the video to infer on
        :param prediction_type: latest, auto or online
            - Latest: return the latest prediction in the database
            - Auto: ask for new inference if latest does not exist of a new model exists
            - Online: always ask for a new inference
        :param task_id: if supplied, prediction will be done for the task with task_id
        :param model_ids: if supplied, prediction is filtered by the model IDs
        :param start_frame: If searching within a range of frames, first index of the range (inclusive).
            A value of None is used to indicate the start of the video.
        :param end_frame: If searching within a range of frames, last index of the range (inclusive).
            A value of None is used to indicate the end of the video.
        :param frameskip: Stride to use for the search; only frames whose indices are multiple
            of this stride will be considered. If none, defaults to video fps
        :return: Tuples (prediction, tuple of result-media-like metadata items)
            and video prediction properties object
        :raises ProjectNotFoundException: if the project does not exist
        """
        # TODO: CVS-74062
        if prediction_type in [PredictionType.AUTO]:
            raise NotImplementedError(
                "Auto predictions for multiple images/frames at the same time is "
                "disabled at the moment. Auto predictions for one image or video "
                "frame is supported."
            )

        if prediction_type == PredictionType.LATEST:
            limit_predictions = MAX_N_ANNOTATIONS_RETURNED
        else:
            limit_predictions = MAX_N_PREDICTIONS_RETURNED

        # For inferring a single-task pipeline, make it "AnnotationSceneKind.PREDICTION"
        # instead of TASK_PREDICTION
        prediction_kind = PredictionService._get_prediction_kind(model_ids=model_ids, project=project, task_id=task_id)

        start_frame = 0 if start_frame is None else start_frame
        end_frame = video.total_frames if end_frame is None else end_frame
        frameskip = int(video.fps) if frameskip is None else frameskip

        if prediction_type == PredictionType.ONLINE:
            raise ValueError(f"{prediction_type.name} is not supported in PredictionService.get_video_predictions()")

        predictions, total_matching_predictions = AnnotationManager.get_filtered_frame_annotation_scenes(
            dataset_storage_identifier=dataset_storage.identifier,
            video_id=video.id_,
            annotation_kind=prediction_kind,
            start_frame=start_frame,
            end_frame=end_frame,
            frameskip=frameskip,
            limit=limit_predictions,
            task_id=task_id,
            model_ids=model_ids,
        )

        actual_start_frame: int | None = None
        actual_end_frame: int | None = None
        if predictions:
            start_identifier = predictions[0].media_identifier
            end_identifier = predictions[-1].media_identifier
            actual_start_frame = (
                start_identifier.frame_index if isinstance(start_identifier, VideoFrameIdentifier) else None
            )
            actual_end_frame = end_identifier.frame_index if isinstance(end_identifier, VideoFrameIdentifier) else None
        video_prediction_properties = VideoPredictionProperties(
            total_count=len(predictions),
            start_frame=actual_start_frame,
            end_frame=actual_end_frame,
            total_requested_count=total_matching_predictions,
            requested_start_frame=start_frame,
            requested_end_frame=end_frame,
        )

        return predictions, video_prediction_properties

    @staticmethod
    @unified_tracing
    def get_prediction_by_id(
        dataset_storage_identifier: DatasetStorageIdentifier,
        prediction_id: ID,
        media_identifier: MediaIdentifierEntity,
    ) -> AnnotationScene:
        """
        Get the prediction and the result media for the passed media

        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the prediction
        :param prediction_id: ID of the requested prediction
        :param media_identifier: MediaIdentifier of media the prediction belongs to
        :return: AnnotationScene of the prediction
        :raises PredictionNotFoundException if prediction does not exists, or is not a
            prediction for the requested media
        """
        annotation_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
        prediction = annotation_scene_repo.get_by_id(prediction_id)

        if isinstance(prediction, NullAnnotationScene):
            raise PredictionNotFoundException(
                f"The requested prediction could not be found. Prediction ID: `{prediction_id}`."
            )
        if prediction.media_identifier != media_identifier:
            raise PredictionNotFoundException(
                f"The requested prediction does not belong to this media. "
                f"Prediction ID: `{prediction_id}`, "
                f"Media Identifier: `{media_identifier}`."
            )
        if prediction.kind not in {
            AnnotationSceneKind.PREDICTION,
            AnnotationSceneKind.TASK_PREDICTION,
        }:
            raise PredictionNotFoundException(
                f"The requested prediction is not a PREDICTION, "
                f"instead it is a {prediction.kind}. "
                f"Prediction ID: `{prediction_id}`"
            )

        return prediction

    @staticmethod
    @unified_tracing
    def get_prediction_by_type(
        project: Project,
        dataset_storage: DatasetStorage,
        media_identifier: MediaIdentifierEntity,
        prediction_type: PredictionType = PredictionType.ONLINE,
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
    ) -> AnnotationScene:
        """
        Get the prediction and the result media for the passed media

        :param project: The project to get the prediction for
        :param dataset_storage: DatasetStorage the prediction belongs to
        :param media_identifier: Media to infer on
        :param prediction_type: latest, auto or online
            - Latest: return the latest prediction in the database
            - Auto: ask for new inference if latest does not exist of a new model exists
            - Online: always ask for a new inference
        :param task_id: if supplied, prediction will be done for the task with task_id
        :param model_ids: if supplied, prediction is filtered by the model IDs
        :return: Tuple (prediction, list of result media) or None if no prediction found
        :raises NoPredictionsFoundException: if the prediction could not be found
        """
        prediction = PredictionService._get_single_prediction(
            project=project,
            dataset_storage=dataset_storage,
            media_identifier=media_identifier,
            prediction_type=prediction_type,
            task_id=task_id,
            model_ids=model_ids,
        )
        if isinstance(prediction, NullAnnotationScene):
            raise NoPredictionsFoundException(media_identifier.media_id)

        return prediction
