# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
import logging

from communication.rest_views.filtered_dataset_rest_views import FilteredDatasetRESTView
from usecases.dataset_filter import DatasetFilter
from usecases.query_builder import QueryResults

from geti_fastapi_tools.exceptions import BadRequestException
from geti_types import (
    CTX_SESSION_VAR,
    ID,
    DatasetStorageIdentifier,
    ImageIdentifier,
    MediaIdentifierEntity,
    VideoFrameIdentifier,
)
from sc_sdk.entities.media_score import MediaScore, NullMediaScore
from sc_sdk.entities.model_test_result import ModelTestResult
from sc_sdk.entities.project import Project
from sc_sdk.utils.annotation_scene_state_helper import AnnotationStatePerTask

logger = logging.getLogger(__name__)


class MediaScoreRESTViews:
    @classmethod
    def media_scores_to_rest(  # noqa: PLR0913
        cls,
        project: Project,
        model_test_result: ModelTestResult,
        query_results: QueryResults,
        dataset_filter: DatasetFilter,
        media_annotation_states_per_task: dict[MediaIdentifierEntity, AnnotationStatePerTask],
        media_score_per_media_identifier: dict[MediaIdentifierEntity, MediaScore],
        annotation_id_per_media_identifier: dict[MediaIdentifierEntity, ID],
        prediction_id_per_media_identifier: dict[MediaIdentifierEntity, ID],
    ) -> dict:
        """
        Converts media identifiers from a media score filter to a rest message.

        :param project: project the media identifiers belong to
        :param query_results: object containing media identifiers and counts per media type
        :param dataset_filter: DatasetFilter object that was used to get the query results
        :param model_test_result: ModelTestResult object, if supplied, we add scores and annotation ids
        :param media_annotation_states_per_task: annotations states associated with the media identifiers
        :return: REST representation of a filtered dataset
        """
        session = CTX_SESSION_VAR.get()
        organization_id = session.organization_id
        workspace_id = session.workspace_id
        media_identifier: MediaIdentifierEntity
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id,
            project_id=project.id_,
            dataset_storage_id=model_test_result.dataset_storage_ids[0],
        )
        rest_views = FilteredDatasetRESTView().get_rest_media_from_query_results(
            dataset_storage_identifier=dataset_storage_identifier,
            query_results=query_results,
            media_annotation_states_per_task=media_annotation_states_per_task,
        )

        for item in rest_views["media"]:
            item_type = item["type"]
            if item_type == "image":
                media_identifier = ImageIdentifier(image_id=ID(item["id"]))
            elif item_type == "video_frame":
                media_identifier = VideoFrameIdentifier(video_id=ID(item["video_id"]), frame_index=item["frame_index"])
            else:
                raise BadRequestException(f"Unsupported media identifier `{item_type}` after score filtering.")

            item["test_result"] = cls._get_test_result_info(
                model_test_result=model_test_result,
                media_identifier=media_identifier,
                media_score=media_score_per_media_identifier[media_identifier],
                annotation_id=annotation_id_per_media_identifier[media_identifier],
                prediction_id=prediction_id_per_media_identifier[media_identifier],
            )

        if len(query_results.media_identifiers) == dataset_filter.limit:
            next_page = (
                f"/api/v1/organizations/{str(organization_id)}/workspaces/{str(workspace_id)}/projects/{str(project.id_)}"
                f"/tests/{str(model_test_result.id_)}/results:query?limit={str(dataset_filter.limit)}"
                f"&skip={str(query_results.skip)}&sort_by={dataset_filter.sort_by.name.lower()}"
                f"&sort_direction={dataset_filter.sort_direction.name.lower()}"
            )
            rest_views["next_page"] = next_page

        return rest_views

    @staticmethod
    def _get_test_result_info(
        model_test_result: ModelTestResult,
        media_identifier: MediaIdentifierEntity,
        media_score: MediaScore,
        annotation_id: ID,
        prediction_id: ID,
    ) -> dict:
        """
        Get info of the test result for a 2D media item, image or video frame

        :param model_test_result: ModelTestResult object representing the test
        :param media_identifier: MediaIdentifierEntity representing the media
        :param media_score: MediaScore object for the given media identifier
        :param annotation_id: latest ground truth annotation id for the media
        :param prediction_id: latest prediction id for the media
        :return: dict containing information about the test result for this specific media item
        """
        ground_truth_dataset_id = model_test_result.ground_truth_dataset_id
        prediction_dataset_id = model_test_result.prediction_dataset_id
        if prediction_dataset_id is None or ground_truth_dataset_id is None:
            raise ValueError(
                f"Ground truth and/or prediction dataset not yet set "
                f"for model test result with id '{model_test_result.id_}'"
            )
        if isinstance(media_score, NullMediaScore):
            raise ValueError(
                f"Media score for media identifier '{media_identifier}' "
                f"is not found for model test result with id '{model_test_result.id_}'"
            )
        scores_rest = []
        for score in list(media_score.scores):
            scores_rest.append(
                {
                    "name": score.name.capitalize(),
                    "value": score.value,
                    "label_id": str(score.label_id) if score.label_id is not None else None,
                }
            )
        return {
            "annotation_id": str(annotation_id),
            "prediction_id": str(prediction_id),
            "scores": scores_rest,
        }
