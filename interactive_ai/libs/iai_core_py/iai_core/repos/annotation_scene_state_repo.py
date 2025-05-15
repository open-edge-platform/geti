# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the MongoDB repo for the annotation scene state entity"""

from collections.abc import Callable, Sequence

import pymongo
from pymongo import IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core.entities.annotation_scene_state import AnnotationSceneState, AnnotationState, NullAnnotationSceneState
from iai_core.repos.base import DatasetStorageBasedSessionRepo
from iai_core.repos.mappers.cursor_iterator import CursorIterator
from iai_core.repos.mappers.mongodb_mappers.annotation_scene_state_mapper import AnnotationSceneStateToMongo
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo

from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, Session


class AnnotationSceneStateRepo(DatasetStorageBasedSessionRepo[AnnotationSceneState]):
    """
    Repository to persist AnnotationSceneState entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    collection_name = "annotation_scene_state"

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name=AnnotationSceneStateRepo.collection_name,
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def forward_map(self) -> Callable[[AnnotationSceneState], dict]:
        return AnnotationSceneStateToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], AnnotationSceneState]:
        return AnnotationSceneStateToMongo.backward

    @property
    def null_object(self) -> NullAnnotationSceneState:
        return NullAnnotationSceneState()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=AnnotationSceneStateToMongo,
            parameter=None,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("media_identifier", pymongo.DESCENDING)]),
            IndexModel([("media_identifier.media_id", pymongo.DESCENDING)]),
            IndexModel([("annotation_scene_id", pymongo.DESCENDING)]),
        ]
        return super_indexes + new_indexes

    def delete_all_by_media_id(self, media_id: ID) -> None:
        """
        Delete all AnnotationSceneState that belong to a given media.

        :param media_id: ID of the media to delete entities for
        """
        query = {"media_identifier.media_id": IDToMongo.forward(media_id)}
        self.delete_all(extra_filter=query)

    def get_all_by_state_for_task(
        self, matchable_annotation_states_per_task: dict[ID, Sequence[AnnotationState]]
    ) -> CursorIterator[AnnotationSceneState]:
        """
        Find all the annotation scene states matching a certain state for one or
        more tasks.

        The query can be extended to multiple tasks, and for each task it is possible
        to specify a set of states that can match.

        Example: find all the annotation scene states of media that are annotated for
        a certain task and unannotated for another one.

        :param matchable_annotation_states_per_task: Dict mapping each task ID to the
            list of annotation states that can match for that task when filtering.
        :return: AnnotationSceneState CursorIterator
        """
        latest_only_query = self._build_query_filter_latest_only()
        match_states_query = self._build_query_match_annotation_states_per_task(
            matchable_annotation_states_per_task=matchable_annotation_states_per_task
        )
        pipeline = [
            *latest_only_query,
            *match_states_query,
            {"$sort": {"_id": 1}},
            {"$replaceRoot": {"newRoot": "$annotation_scene_state"}},
        ]
        cursor = self.aggregate_read(pipeline)
        return self.cursor_wrapper(cursor)

    def count_images_state_for_task(self, annotation_states: Sequence[AnnotationState], task_id: ID) -> int:
        """
        Counts the number of images with a certain state for a task.

        :param annotation_states: sequence of annotations states to filter on
        :param task_id: ID of the task to filter the AnnotationState for.
        :return: number of the matching images
        """
        latest_only_query = self._build_query_filter_latest_only()
        match_state_query = self._build_query_match_annotation_states_per_task(
            matchable_annotation_states_per_task={task_id: annotation_states}
        )
        count_images_query = self._build_query_count_media(media_type="image")
        pipeline = [*latest_only_query, *match_state_query, *count_images_query]
        docs = list(self.aggregate_read(pipeline))
        return docs[0]["count"] if docs else 0

    def count_video_frames_state_for_task(self, annotation_states: Sequence[AnnotationState], task_id: ID) -> int:
        """
        Counts the number of video frames with a certain state for a task.

        :param annotation_states: sequence of annotations states to filter on
        :param task_id: ID of the task to filter the AnnotationState for.
        :return: number of the matching video frames
        """
        latest_only_query = self._build_query_filter_latest_only()
        match_state_query = self._build_query_match_annotation_states_per_task(
            matchable_annotation_states_per_task={task_id: annotation_states}
        )
        count_images_query = self._build_query_count_media(media_type="video_frame")
        pipeline = [*latest_only_query, *match_state_query, *count_images_query]
        docs = list(self.aggregate_read(pipeline))
        return docs[0]["count"] if docs else 0

    def count_videos_state_for_task(self, annotation_states: list[AnnotationState], task_id: ID) -> int:
        """
        Counts the number of videos with a certain state for a task.

        :param annotation_states: List of AnnotationState to filter on
        :param task_id: ID of the task to filter the AnnotationState for.
        :return: number of the matching videos
        """
        latest_only_query = self._build_query_filter_latest_only()
        match_state_query = self._build_query_match_annotation_states_per_task(
            matchable_annotation_states_per_task={task_id: annotation_states}
        )
        count_images_query = self._build_query_count_media(media_type="video")
        pipeline = [*latest_only_query, *match_state_query, *count_images_query]
        docs = list(self.aggregate_read(pipeline))
        return docs[0]["count"] if docs else 0

    def get_latest_by_media_identifiers(
        self, media_identifiers: list[MediaIdentifierEntity]
    ) -> dict[MediaIdentifierEntity, AnnotationSceneState]:
        """
        For each media identifier in a list, get the most recent AnnotationSceneState in the repo.

        :param media_identifiers: List of media identifiers to get the states for
        :return: Dict with a AnnotationSceneState for each identifier
        """
        pipeline: list[dict] = [
            {
                "$match": {
                    "media_identifier": {
                        "$in": [MediaIdentifierToMongo.forward(identifier) for identifier in media_identifiers]
                    }
                }
            },
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$media_identifier",
                    "annotation_scene_state": {"$last": "$$ROOT"},
                }
            },
        ]
        pipeline_results = self.aggregate_read(pipeline)
        annotation_scene_states = [
            self.backward_map(pipeline_result["annotation_scene_state"]) for pipeline_result in pipeline_results
        ]
        # Convert result to a dictionary that maps each media identifier to a annotation scene state
        image_and_frame_states_dict: dict[MediaIdentifierEntity, AnnotationSceneState] = {
            state.media_identifier: state for state in annotation_scene_states
        }
        # Add NullAnnotationSceneState for all identifiers that didn't find a state
        null_states_dict: dict[MediaIdentifierEntity, AnnotationSceneState] = {
            identifier: NullAnnotationSceneState()
            for identifier in media_identifiers
            if identifier not in image_and_frame_states_dict
        }
        image_and_frame_states_dict.update(null_states_dict)
        return image_and_frame_states_dict

    def get_latest_for_annotation_scenes(self, annotation_scene_ids: list[ID]) -> dict[ID, AnnotationSceneState]:
        """
        For each annotation scene ID in a list, get the most recent AnnotationSceneState in the repo.

        :param annotation_scene_ids: List of annotation scene IDs to get the states for
        :return: Dict with a AnnotationSceneState for each identifier
        """
        pipeline: list[dict] = [
            {
                "$match": {
                    "annotation_scene_id": {
                        "$in": [IDToMongo.forward(annotation_scene_id) for annotation_scene_id in annotation_scene_ids]
                    }
                }
            },
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$annotation_scene_id",
                    "annotation_scene_state": {"$last": "$$ROOT"},
                }
            },
        ]
        pipeline_results = self.aggregate_read(pipeline)
        annotation_scene_states = [
            self.backward_map(pipeline_result["annotation_scene_state"]) for pipeline_result in pipeline_results
        ]
        # Convert result to a dictionary that maps each annotation scene ID to a annotation scene state
        return {state.annotation_scene_id: state for state in annotation_scene_states}

    def get_latest_for_annotation_scene(self, annotation_scene_id: ID) -> AnnotationSceneState:
        """
        Get the most recent AnnotationSceneState in the repo for the annotation scene
        with a given `annotation_scene_id`.

        :param annotation_scene_id: ID of the AnnotationScene to get the state for.
        :return: AnnotationSceneState for the annotation_scene
        """
        query = {"annotation_scene_id": IDToMongo.forward(annotation_scene_id)}
        return self.get_one(extra_filter=query, latest=True)

    @staticmethod
    def _build_query_filter_latest_only() -> list[dict]:
        """
        Create a query that filters the latest annotation scene state for every media identifier.

        :return: Query that filters the latest annotation scene state for every media identifier.
        """
        return [
            {
                "$group": {
                    "_id": "$media_identifier",
                    "annotation_scene_state": {"$last": "$$ROOT"},
                }
            }
        ]

    @staticmethod
    def _build_query_match_annotation_states_per_task(
        matchable_annotation_states_per_task: dict[ID, Sequence[AnnotationState]],
    ) -> list[dict]:
        """
        Create a query that matches annotation states with the per-task states defined in the input dictionary.

        :param matchable_annotation_states_per_task: For each task, a list of AnnotationStates that should be matched
        :return: Query that filters the annotation scene states that fit the filter
        """
        return [
            {
                "$match": {
                    "annotation_scene_state.state_per_task": {
                        "$elemMatch": {
                            "task_id": IDToMongo.forward(task_id),
                            "annotation_state": {"$in": [str(ann_state) for ann_state in ann_states]},
                        }
                    }
                }
            }
            for task_id, ann_states in matchable_annotation_states_per_task.items()
        ]

    @staticmethod
    def _build_query_count_media(media_type: str) -> list:
        """
        Create a query that matches annotation states whose media identifier has the input media_type, and then counts
        the number of states for that media type

        :param media_type: Type of media to count the number of annotation scene states for
        :return: Query that matches the annotation state for the media type and counts them.
        """
        if media_type == "video":
            query = [
                {"$match": {"annotation_scene_state.media_identifier.type": "video_frame"}},
                {"$group": {"_id": "$_id.media_id"}},
                {"$count": "count"},
            ]
        else:
            query = [
                {"$match": {"annotation_scene_state.media_identifier.type": media_type}},
                {"$group": {"_id": "$annotation_scene_state.media_identifier"}},
                {"$count": "count"},
            ]
        return query
