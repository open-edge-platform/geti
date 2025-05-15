# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the PredictionRESTViews class, to convert prediction entities to
their REST representation
"""

from collections.abc import Sequence
from typing import Any

from communication.views.annotation_rest_views import ANNOTATIONS, LABELS, AnnotationRESTViews
from communication.views.scored_label_rest_views import ScoredLabelRESTViews
from entities import PredictionType
from entities.video_prediction_properties import VideoPredictionProperties

from geti_telemetry_tools import unified_tracing
from geti_types import ID
from iai_core.entities.annotation import AnnotationScene
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.model_template import TaskType
from iai_core.entities.project import Project
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Rectangle


class PredictionRESTViews(AnnotationRESTViews):
    """
    This class contains methods to convert a prediction to its REST representation.

    Predictions are represented as AnnotationScene, with it's `kind` set to
    `AnnotationSceneKind.PREDICTION` or `AnnotationSceneKind.TASK_PREDICTION`. Because
    of this, this class inherits most of it's methods from AnnotationRESTViews.
    """

    @unified_tracing
    @staticmethod
    def media_2d_prediction_to_rest(
        prediction: AnnotationScene,
        project: Project,
        label_schema: LabelSchema,
        label_only: bool = False,
        is_ephemeral: bool = False,
        update_response_for_inference_gateway: bool = False,
    ) -> dict:
        """
        Returns the REST representation of a Prediction.

        :param prediction: the input prediction to be represented in REST
        :param project: project to which the prediction belongs. It is used to check
            whether the project consist of a single rotated detection task
        :param label_schema: label schema of the project
        :param is_ephemeral: if set to true, skip rest mapping of media identifier
        :param label_only: if set to true, do not return the shape
        :param update_response_for_inference_gateway: bool to indicate if response should be
            updated to new inference gateway REST schema
        :return: the REST representation of the prediction.
        """
        trainable_tasks = project.get_trainable_task_nodes()
        is_rotated_detection = (
            len(trainable_tasks) == 1 and trainable_tasks[0].task_properties.task_type == TaskType.ROTATED_DETECTION
        )
        result = PredictionRESTViews.media_2d_annotation_to_rest(
            annotation_scene=prediction,
            label_only=label_only,
            is_rotated_detection=is_rotated_detection,
            deleted_label_ids=label_schema.deleted_label_ids,
            is_ephemeral=is_ephemeral,
        )

        # Ensure that for global shapes with no label the empty label is added
        # This can happen when the predicted label is a deleted label
        for annotation_rest, annotation in zip(result[ANNOTATIONS], prediction.annotations):
            if len(annotation_rest.get(LABELS, [])) == 0 and Rectangle.is_full_box(annotation.shape):
                empty_label = next(label for label in label_schema.get_all_labels() if label.is_empty)
                annotation_rest[LABELS] = [
                    ScoredLabelRESTViews.scored_label_to_rest(
                        ScoredLabel(label_id=empty_label.id_, is_empty=True, probability=1.0)
                    )
                ]
        if update_response_for_inference_gateway:
            return PredictionRESTViews._update_prediction_rest_for_inference_gateway(result)
        return result

    @staticmethod
    def _update_prediction_rest_for_inference_gateway(
        prediction_rest_view: dict,
    ) -> dict:
        """
        Updates the REST representation of a Prediction for inference gateway.

        - rename annotations to predictions
            - predictions only contain labels and shapes
                - labels only contain id and probability
        - renames modified to created
        - keeps media_identifier and removes all other additional fields:
            for example: kind, annotation_state, etc
        """
        return {
            "predictions": [
                PredictionRESTViews._update_annotation_rest_for_inference_gateway(annotation_rest_view)
                for annotation_rest_view in prediction_rest_view["annotations"]
            ],
            "media_identifier": prediction_rest_view["media_identifier"],
            "created": prediction_rest_view["modified"],
        }

    @staticmethod
    def _update_annotation_rest_for_inference_gateway(
        annotation_rest_view: dict,
    ) -> dict:
        return {
            "labels": [
                PredictionRESTViews._update_label_rest_for_inference_gateway(label_rest_view)
                for label_rest_view in annotation_rest_view["labels"]
            ],
            "shape": annotation_rest_view["shape"],
        }

    @staticmethod
    def _update_label_rest_for_inference_gateway(
        label_rest_view: dict,
    ) -> dict:
        return {
            "id": label_rest_view["id"],
            "probability": label_rest_view["probability"],
        }

    @staticmethod
    def media_2d_predictions_to_rest(  # noqa: PLR0913
        organization_id: ID,
        predictions: Sequence[AnnotationScene],
        project: Project,
        dataset_storage_id: ID,
        label_schema: LabelSchema,
        video_prediction_properties: VideoPredictionProperties,
        prediction_type: PredictionType,
        video_id: ID,
        video_fps: float,
        frameskip: int | None = None,
        label_only: bool = False,
        task_id: ID | None = None,
        model_id: ID | None = None,
    ) -> dict[str, Any]:
        """
        Returns the REST representation of a list of predictions, used for video predictions.

        :param organization_id: ID of the organization
        :param predictions: list of predictions
        :param project: project to which the predictions belong to. It is used to check
            whether the project consist of a single rotated detection task
        :param dataset_storage_id: the dataset storage to which the result media belong
        :param label_schema: label schema of the project
        :param video_prediction_properties: the video prediction properties for this rest view
        :param prediction_type: Prediction type used to generate the predictions
        :param video_id: ID of the video that predictions were generated for.
        :param video_fps: frames per second of the video
        :param frameskip: frameskip used to generate predictions.
        :param label_only: if set to true, do not return the shape
        :return: the REST representation of the predictions.
        """
        prediction_list = []
        for prediction in predictions:
            # todo: check if this is slow, maybe the result media pulling can be optimized
            prediction_rest = PredictionRESTViews.media_2d_prediction_to_rest(
                prediction=prediction,
                project=project,
                label_schema=label_schema,
                label_only=label_only,
            )
            if model_id is None:
                prediction_rest["maps"] = []
            prediction_list.append(prediction_rest)

        video_predictions = "video_predictions" if model_id is None else "batch_predictions"
        response = {
            video_predictions: prediction_list,
            "video_prediction_properties": PredictionRESTViews.video_prediction_properties_to_rest(
                video_prediction_properties=video_prediction_properties,
            ),
        }

        if (
            video_prediction_properties.total_count < video_prediction_properties.total_requested_count
        ) and video_prediction_properties.end_frame is not None:
            next_start_frame = (
                video_prediction_properties.end_frame + frameskip
                if frameskip is not None
                else video_prediction_properties.end_frame + video_fps
            )
            next_page = (
                f"/api/v1/organizations/{str(organization_id)}/workspaces/{str(project.workspace_id)}"
                f"/projects/{str(project.id_)}/datasets/{str(dataset_storage_id)}"
                f"/media/videos/{str(video_id)}/predictions/{prediction_type.name.lower()}?"
                f"label_only={str(label_only).lower()}"
                f"&start_frame={int(next_start_frame)}"
            )
            if video_prediction_properties.requested_end_frame is not None:
                next_page += f"&end_frame={video_prediction_properties.requested_end_frame}"
            if frameskip is not None:
                next_page += f"&frameskip={frameskip}"
            if task_id is not None:
                next_page += f"&task_id={str(task_id)}"
            if model_id is not None:
                next_page += f"&model_id={str(model_id)}"

            response["next_page"] = next_page
        return response

    @staticmethod
    def video_prediction_properties_to_rest(
        video_prediction_properties: VideoPredictionProperties,
    ) -> dict[str, Any]:
        """
        Return a dict with the rest representation for the video pagination properties.
        :param video_prediction_properties: the pagination properties to be represented in REST
        :return: the REST representation of the video prediction properties
        """
        return {
            "total_count": video_prediction_properties.total_count,
            "start_frame": video_prediction_properties.start_frame,
            "end_frame": video_prediction_properties.end_frame,
            "total_requested_count": video_prediction_properties.total_requested_count,
            "requested_start_frame": video_prediction_properties.requested_start_frame,
            "requested_end_frame": video_prediction_properties.requested_end_frame,
        }
