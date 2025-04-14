# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the PredictionController class
"""

from typing import Any

from communication.exceptions import NoModelTrainedException, NoPredictionsFoundException, VideoNotFoundException
from communication.views.prediction_rest_views import PredictionRESTViews
from entities import PredictionType
from service.label_schema_service import LabelSchemaService
from service.prediction_service import PredictionService
from service.project_service import ProjectService

from geti_telemetry_tools import unified_tracing
from geti_types import ID, MediaIdentifierEntity
from sc_sdk.entities.project import Project
from sc_sdk.entities.video import NullVideo
from sc_sdk.repos import VideoRepo
from sc_sdk.services import ModelService


class PredictionController:
    @staticmethod
    @unified_tracing
    def get_video_predictions(  # noqa: PLR0913
        organization_id: ID,
        project_id: ID,
        dataset_id: ID,
        video_id: ID,
        prediction_type: PredictionType,
        task_id: ID | None = None,
        model_id: ID | None = None,
        label_only: bool = False,
        start_frame: int | None = None,
        end_frame: int | None = None,
        frameskip: int | None = None,
    ) -> dict[str, Any]:
        """
        Get a prediction and result media for each video frame of a video.

        This makes it possible to pull a different annotation revision over REST.

        :param organization_id: ID of the organization
        :param project_id: ID of project the image belongs to
        :param dataset_id: ID of the dataset the image belongs to
        :param video_id: ID of video
        :param prediction_type: latest, auto, or online.
            - Latest: pull the latest one in the database
            - Auto: send an inference request if there is no prediction in the database
            - Online: always sends a inference request
        :param task_id: ID of the task to do the inference.
            If None, then prediction is done on pipeline
        :param model_id: ID of the model to use for the prediction
            Currently only supported if prediction type is latest.
        :param label_only: if set to true, do not return the shape of the prediction
        :param start_frame: If searching within a range of frames, first index of the range (inclusive).
            A value of None is used to indicate the start of the video.
        :param end_frame: If searching within a range of frames, last index of the range (inclusive).
            A value of None is used to indicate the end of the video.
        :param frameskip: Stride to use for the search; only frames whose indices are multiple
            of this stride will be considered. If none, defaults to video fps.
        :return: REST View or error response
        """
        project = ProjectService.get_by_id(project_id=project_id)
        dataset_storage = ProjectService.get_dataset_storage_by_id(project=project, dataset_storage_id=dataset_id)
        video = VideoRepo(dataset_storage.identifier).get_by_id(video_id)
        if isinstance(video, NullVideo):
            raise VideoNotFoundException(video_id=video_id, dataset_storage_id=dataset_storage.id_)

        filtering_model_ids = PredictionController._get_model_ids(
            model_id=model_id, prediction_type=prediction_type, project=project, task_id=task_id
        )

        (
            predictions,
            video_prediction_properties,
        ) = PredictionService.get_video_predictions(
            project=project,
            dataset_storage=dataset_storage,
            video=video,
            prediction_type=prediction_type,
            task_id=task_id,
            model_ids=filtering_model_ids,
            start_frame=start_frame,
            end_frame=end_frame,
            frameskip=frameskip,
        )
        if len(predictions) == 0:
            raise NoPredictionsFoundException(media_id=video_id)

        label_schema = LabelSchemaService.get_latest_label_schema_for_project(project.identifier)

        return PredictionRESTViews.media_2d_predictions_to_rest(
            organization_id=organization_id,
            predictions=predictions,
            project=project,
            dataset_storage_id=dataset_id,
            label_schema=label_schema,
            video_prediction_properties=video_prediction_properties,
            label_only=label_only,
            prediction_type=prediction_type,
            video_id=video_id,
            video_fps=video.fps,
            frameskip=frameskip,
            task_id=task_id,
            model_id=model_id,
        )

    @staticmethod
    @unified_tracing
    def get_prediction(  # noqa: PLR0913
        project_id: ID,
        dataset_storage_id: ID,
        media_identifier: MediaIdentifierEntity,
        prediction_id: ID | None = None,
        prediction_type: PredictionType | None = None,
        task_id: ID | None = None,
        model_id: ID | None = None,
        label_only: bool = False,
        for_inf_gateway: bool = False,
    ) -> dict[str, Any]:
        """
        Get a prediction and result media for a media identifier

        :param project_id: ID of project the image belongs to
        :param dataset_storage_id: ID of the dataset storage the image belongs to
        :param media_identifier: Media identifier to get the prediction for
        :param prediction_id: ID of requested prediction
            If none, prediction_type should be given
        :param prediction_type: PredictionType (latest, auto, or online)
            If None, prediction_id should be given.
            - Latest: pull the latest one in the database
            - Auto: send an inference request if there is no prediction in the database
            - Online: always sends an inference request
        :param task_id: ID of the task to do the inference.
            If None, then prediction is done on pipeline
        :param model_id: ID of the model to use for the prediction
            Currently only supported if prediction type is latest.
        :param label_only: if set to true, do not return the shape of the prediction
        :param for_inf_gateway: if set to true, map the response to the new inference gateway schema
        :return: REST View or error response
        """
        project = ProjectService.get_by_id(project_id=project_id)
        dataset_storage = ProjectService.get_dataset_storage_by_id(project, dataset_storage_id)

        filtering_model_ids = PredictionController._get_model_ids(
            model_id=model_id, prediction_type=prediction_type, project=project, task_id=task_id
        )

        if prediction_id is not None:
            prediction = PredictionService.get_prediction_by_id(
                dataset_storage_identifier=dataset_storage.identifier,
                prediction_id=prediction_id,
                media_identifier=media_identifier,
            )
        elif prediction_type is not None:
            prediction = PredictionService.get_prediction_by_type(
                project=project,
                dataset_storage=dataset_storage,
                media_identifier=media_identifier,
                prediction_type=prediction_type,
                task_id=task_id,
                model_ids=filtering_model_ids,
            )
        else:
            raise ValueError("Either prediction_id or prediction_type should be not None.")

        label_schema = LabelSchemaService.get_latest_label_schema_for_project(project.identifier)

        prediction_rest = PredictionRESTViews.media_2d_prediction_to_rest(
            prediction=prediction,
            project=project,
            label_schema=label_schema,
            label_only=label_only,
            update_response_for_inference_gateway=for_inf_gateway,
        )
        if not for_inf_gateway:
            prediction_rest["maps"] = []

        return prediction_rest

    @staticmethod
    def _get_model_ids(
        model_id: ID | None, prediction_type: PredictionType | None, project: Project, task_id: ID | None
    ) -> set[ID]:
        """
        Return the set of model ids to filter predictions on.

        If model_id is given, returns model_id. If task_id is specified, it returns the active model id for
        that task. Else it gets the active inference model id for each task.
        """
        model_ids: set[ID]
        if model_id is not None:
            if prediction_type is not PredictionType.LATEST:
                raise ValueError("A model_id can only be specified for prediction type latest.")
            model_ids = {model_id}
        else:
            task_node_ids = [t.id_ for t in project.get_trainable_task_nodes()] if task_id is None else [task_id]
            model_ids_ = [
                ModelService.get_inference_active_model(
                    project_identifier=project.identifier,
                    task_node_id=task_node_id,
                ).id_
                for task_node_id in task_node_ids
            ]

            for task_node_id, model_id in zip(task_node_ids, model_ids_):  # noqa: PLR1704
                if model_id == ID():
                    raise NoModelTrainedException
            model_ids = set(model_ids_)
        return model_ids
