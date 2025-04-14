# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any

from communication.rest_views.media_rest_views import MediaRESTViews
from usecases.dataset_filter import DatasetFilter
from usecases.query_builder import MatchedFramesVideoIdentifier, MediaQueryResult, QueryResults

from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, MediaIdentifierEntity, MediaType
from sc_sdk.entities.video import Video
from sc_sdk.utils.annotation_scene_state_helper import AnnotationStatePerTask


class FilteredDatasetRESTView:
    @classmethod
    @unified_tracing
    def filtered_dataset_storage_to_rest(
        cls,
        dataset_storage_identifier: DatasetStorageIdentifier,
        query_results: QueryResults,
        dataset_filter: DatasetFilter,
        media_annotation_states_per_task: dict[MediaIdentifierEntity, AnnotationStatePerTask],
    ) -> dict:
        """
        Converts media identifiers from an advanced dataset filter to a rest message.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the media
        :param query_results: object containing media identifiers and counts per media type
        :param dataset_filter: DatasetFilter object that was used to get the query results
        :param media_annotation_states_per_task: annotations states associated with the media identifiers
        :return: REST representation of a filtered dataset
        """
        rest_views = FilteredDatasetRESTView.get_rest_media_from_query_results(
            dataset_storage_identifier=dataset_storage_identifier,
            query_results=query_results,
            media_annotation_states_per_task=media_annotation_states_per_task,
        )
        session = CTX_SESSION_VAR.get()
        organization_id = session.organization_id
        workspace_id = dataset_storage_identifier.workspace_id
        project_id = dataset_storage_identifier.project_id
        dataset_storage_id = dataset_storage_identifier.dataset_storage_id

        if len(query_results.media_query_results) == dataset_filter.limit:
            next_page = (
                f"/api/v1/organizations/{str(organization_id)}/workspaces/{str(workspace_id)}/projects/{str(project_id)}"
                f"/datasets/{str(dataset_storage_id)}/media:query?limit={str(dataset_filter.limit)}"
                f"&skip={str(query_results.skip)}&sort_by={dataset_filter.sort_by.name.lower()}"
                f"&sort_direction={dataset_filter.sort_direction.name.lower()}"
            )
            rest_views["next_page"] = next_page

        return rest_views

    @classmethod
    @unified_tracing
    def filtered_dataset_to_rest(
        cls,
        dataset_storage_identifier: DatasetStorageIdentifier,
        query_results: QueryResults,
        dataset_filter: DatasetFilter,
        dataset_id: ID,
        media_annotation_states_per_task: dict[MediaIdentifierEntity, AnnotationStatePerTask],
    ) -> dict:
        """
        Converts media identifiers from an advanced dataset filter to a rest message.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the media
        :param query_results: object containing media identifiers and counts per media type
        :param dataset_filter: DatasetFilter object that was used to get the query results
        :param dataset_id: ID of the dataset that was filtered
        :param media_annotation_states_per_task: annotations states associated with the media identifiers
        :return: REST representation of a filtered dataset
        """
        rest_views = FilteredDatasetRESTView.get_rest_media_from_query_results(
            dataset_storage_identifier=dataset_storage_identifier,
            query_results=query_results,
            media_annotation_states_per_task=media_annotation_states_per_task,
        )

        session = CTX_SESSION_VAR.get()
        organization_id = session.organization_id
        workspace_id = dataset_storage_identifier.workspace_id
        project_id = dataset_storage_identifier.project_id
        dataset_storage_id = dataset_storage_identifier.dataset_storage_id

        if len(query_results.media_query_results) == dataset_filter.limit:
            next_page = (
                f"/api/v1/organizations/{str(organization_id)}/workspaces/{str(workspace_id)}/projects/{str(project_id)}"
                f"/datasets/{str(dataset_storage_id)}/training_revisions/{dataset_id}/"
                f"media:query?limit={str(dataset_filter.limit)}&skip="
                f"{str(query_results.skip)}&sort_by={dataset_filter.sort_by.name.lower()}"
                f"&sort_direction={dataset_filter.sort_direction.name.lower()}"
            )
            rest_views["next_page"] = next_page

        return rest_views

    @classmethod
    @unified_tracing
    def filtered_dataset_for_video_to_rest(
        cls,
        dataset_storage_identifier: DatasetStorageIdentifier,
        query_results: QueryResults,
        dataset_filter: DatasetFilter,
        dataset_id: ID,
        video_id: ID,
        media_annotation_states_per_task: dict[MediaIdentifierEntity, AnnotationStatePerTask],
    ) -> dict:
        """
        Converts media identifiers from an advanced dataset filter to a rest message.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the media
        :param query_results: object containing media identifiers and counts per media type
        :param dataset_filter: DatasetFilter object that was used to get the query results
        :param dataset_id: ID of the dataset that was filtered
        :param video_id: ID of the video_id to filter
        :param media_annotation_states_per_task: annotations states associated with the media identifiers
        :return: REST representation of a filtered dataset
        """
        rest_views = FilteredDatasetRESTView.get_rest_media_from_query_results(
            dataset_storage_identifier=dataset_storage_identifier,
            query_results=query_results,
            media_annotation_states_per_task=media_annotation_states_per_task,
        )

        session = CTX_SESSION_VAR.get()
        organization_id = session.organization_id
        workspace_id = dataset_storage_identifier.workspace_id
        project_id = dataset_storage_identifier.project_id
        dataset_storage_id = dataset_storage_identifier.dataset_storage_id

        if len(query_results.media_query_results) == dataset_filter.limit:
            next_page = (
                f"/api/v1/organizations/{str(organization_id)}/workspaces/{str(workspace_id)}/projects/{str(project_id)}"
                f"/datasets/{str(dataset_storage_id)}/training_revisions/{dataset_id}/"
                f"media/videos/{video_id}:query?limit={str(dataset_filter.limit)}&skip="
                f"{str(query_results.skip)}&sort_by={dataset_filter.sort_by.name.lower()}"
                f"&sort_direction={dataset_filter.sort_direction.name.lower()}"
            )
            rest_views["next_page"] = next_page

        return rest_views

    @staticmethod
    @unified_tracing
    def filtered_frames_to_rest(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_frame_indices: list[int],
        query_results: QueryResults,
        dataset_filter: DatasetFilter,
        video: Video,
        media_annotation_states_per_task: dict[MediaIdentifierEntity, AnnotationStatePerTask],
        include_frame_details: bool,
    ) -> dict:
        """
        Converts media identifiers from an advanced dataset filter to a rest message.

        :param dataset_storage_identifier: dataset storage containing the video
        :param video_frame_indices: List of integers indicating matched video frame indices
        :param query_results: object containing media identifiers and counts per media type
        :param dataset_filter: DatasetFilter object that was used to get the query results
        :param video: Video that has been filtered
        :param media_annotation_states_per_task: annotations states associated with the media identifiers
        :param include_frame_details: bool indicating whether frame details should be included
            in the REST view
        :return: REST representation of a filtered dataset
        """
        session = CTX_SESSION_VAR.get()
        organization_id = session.organization_id
        workspace_id = dataset_storage_identifier.workspace_id
        project_id = dataset_storage_identifier.project_id
        dataset_storage_id = dataset_storage_identifier.dataset_storage_id

        rest_views = FilteredDatasetRESTView.get_rest_video_frames_from_query_results(
            dataset_storage_identifier=dataset_storage_identifier,
            video_frame_indices=video_frame_indices,
            query_results=query_results,
            media_annotation_states_per_task=media_annotation_states_per_task,
            include_frame_details=include_frame_details,
        )
        rest_views["video_information"] = {
            "height": video.height,
            "width": video.width,
            "frame_count": video.total_frames,
            "frame_stride": video.stride,
            "frame_rate": video.fps,
            "duration": video.duration,
            "size": video.size,
            "display_url": f"/api/v1/organizations/{str(organization_id)}/workspaces/{str(workspace_id)}"
            f"/projects/{str(project_id)}/datasets/"
            f"{str(dataset_storage_id)}/media/videos/{str(video.id_)}/display/stream",
        }

        if len(query_results.media_query_results) == dataset_filter.limit:
            next_page = (
                f"/api/v1/organizations/{str(organization_id)}/workspaces/{str(workspace_id)}/projects/{str(project_id)}"
                f"/datasets/{str(dataset_storage_id)}/media/videos/{video.id_}:query?"
                f"limit={str(dataset_filter.limit)}&skip={str(query_results.skip)}"
            )
            rest_views["next_page"] = next_page

        return rest_views

    @staticmethod
    def get_rest_media_from_query_results(
        dataset_storage_identifier: DatasetStorageIdentifier,
        query_results: QueryResults,
        media_annotation_states_per_task: dict[MediaIdentifierEntity, AnnotationStatePerTask],
    ) -> dict[str, Any]:
        """
        Converts media identifiers from a query result to a rest message.

        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the media
        :param query_results: object containing media identifiers and counts per media type
        :param media_annotation_states_per_task: annotations states associated with the media identifiers
        :return: REST representation of a filtered dataset
        """
        return {
            "media": [
                FilteredDatasetRESTView._get_rest_view_for_media_query_result(
                    media_annotation_states_per_task=media_annotation_states_per_task,
                    dataset_storage_identifier=dataset_storage_identifier,
                    media_query_result=media_query_result,
                )
                for media_query_result in query_results.media_query_results
            ],
            "total_matched_images": query_results.matching_images_count,
            "total_matched_videos": query_results.matching_videos_count,
            "total_matched_video_frames": query_results.matching_video_frames_count,
            "total_images": query_results.total_images_count,
            "total_videos": query_results.total_videos_count,
        }

    @staticmethod
    def get_rest_video_frames_from_query_results(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_frame_indices: list[int],
        query_results: QueryResults,
        media_annotation_states_per_task: dict[MediaIdentifierEntity, AnnotationStatePerTask],
        include_frame_details: bool,
    ) -> dict[str, Any]:
        """
        Converts video frame identifiers from a query result to a rest message.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the media
        :param video_frame_indices: List of integers indicating matched video frame indices
        :param query_results: object containing media identifiers and counts per media type
        :param media_annotation_states_per_task: Dict mapping each media identifier
            to another dict containing the annotation state for each task
        :param include_frame_details: bool indicating whether frame details should be included
            in the REST view
        :return: REST representation of a filtered dataset
        """
        rest_views: dict = {
            "video_frame_indices": video_frame_indices,
        }

        if include_frame_details:
            rest_views["video_frames"] = [
                MediaRESTViews.media_to_rest(
                    media=media_query_result.media,
                    media_identifier=media_query_result.media_identifier,
                    dataset_storage_identifier=dataset_storage_identifier,
                    annotation_state_per_task=media_annotation_states_per_task.get(
                        media_query_result.media_identifier, {}
                    ),
                )
                for media_query_result in query_results.media_query_results
            ]

        rest_views["total_matched_video_frames"] = query_results.matching_video_frames_count

        return rest_views

    @staticmethod
    def _get_rest_view_for_media_query_result(
        media_annotation_states_per_task: dict[MediaIdentifierEntity, AnnotationStatePerTask],
        dataset_storage_identifier: DatasetStorageIdentifier,
        media_query_result: MediaQueryResult,
    ) -> dict[str, Any]:
        rest_view = MediaRESTViews.media_to_rest(
            media=media_query_result.media,
            media_identifier=media_query_result.media_identifier,
            dataset_storage_identifier=dataset_storage_identifier,
            annotation_state_per_task=media_annotation_states_per_task.get(media_query_result.media_identifier, None),
            video_annotation_statistics=media_query_result.video_annotation_statistics,
        )

        if media_query_result.media_identifier.media_type in {
            MediaType.IMAGE,
            MediaType.VIDEO_FRAME,
        }:
            rest_view["annotation_scene_id"] = media_query_result.annotation_scene_id
            rest_view["roi_id"] = media_query_result.roi_id
            rest_view["last_annotator_id"] = media_query_result.last_annotator_id

        if isinstance(media_query_result.media_identifier, MatchedFramesVideoIdentifier):
            rest_view["matched_frames"] = media_query_result.media_identifier.matched_frames

        return rest_view
