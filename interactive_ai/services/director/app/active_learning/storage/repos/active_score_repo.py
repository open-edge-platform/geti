# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the MongoDB repos for active score entities"""

from collections.abc import Callable, Iterator, Sequence
from typing import Any

import pymongo
from pymongo import IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from active_learning.entities import ActiveScore, ActiveScoreSuggestionInfo, NullActiveScore
from active_learning.storage.mappers.mongodb import ActiveScoreToMongo

from geti_types import (
    ID,
    DatasetStorageIdentifier,
    ImageIdentifier,
    MediaIdentifierEntity,
    Session,
    VideoFrameIdentifier,
    VideoIdentifier,
)
from sc_sdk.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo
from sc_sdk.utils.type_helpers import SequenceOrSet


class ActiveScoreRepo(DatasetStorageBasedSessionRepo[ActiveScore]):
    """
    Repository to persist ActiveScore entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="active_score",
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def forward_map(self) -> Callable[[ActiveScore], dict]:
        return ActiveScoreToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], ActiveScore]:
        return ActiveScoreToMongo.backward

    @property
    def null_object(self) -> NullActiveScore:
        return NullActiveScore()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=ActiveScoreToMongo, parameter=None)

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("media_identifier", pymongo.DESCENDING)]),
            IndexModel([("media_identifier.media_id", pymongo.DESCENDING)]),
            IndexModel([("score", pymongo.ASCENDING)]),
        ]
        return super_indexes + new_indexes

    def get_by_media_identifier(self, media_identifier: MediaIdentifierEntity) -> ActiveScore:
        """
        Get an ActiveScore instance given its media identifier.

        :param media_identifier: Media identifier of the entity to retrieve
        :return: ActiveScore object if found, NullActiveScore otherwise
        """
        query = {"media_identifier": MediaIdentifierToMongo.forward(media_identifier)}
        return self.get_one(extra_filter=query)

    def get_by_media_identifiers(
        self, media_identifiers: SequenceOrSet[MediaIdentifierEntity]
    ) -> dict[MediaIdentifierEntity, ActiveScore]:
        """
        Get the ActiveScore entities corresponding to the given media identifiers.

        Note: the output dict will not contain any entry for non-existing scores.

        :param media_identifiers: Media identifiers to get the scores for
        :return: Dict mapping each media identifier to the relative ActiveScore object
        """
        query = {
            "media_identifier": {
                "$in": [MediaIdentifierToMongo.forward(identifier) for identifier in set(media_identifiers)]
            },
        }
        found_scores = self.get_all(extra_filter=query)
        return {score.media_identifier: score for score in found_scores}

    def delete_by_media_identifier(self, media_identifier: MediaIdentifierEntity) -> None:
        """
        Delete any ActiveScore associated with the given media identifier.

        If the input media is a video, it will also delete its frame-relative entities.

        :param media_identifier: media identifier of the active score to delete
        """
        query: dict[str, Any]
        if isinstance(media_identifier, ImageIdentifier | VideoFrameIdentifier):
            query = {"media_identifier": MediaIdentifierToMongo.forward(media_identifier)}
        elif isinstance(media_identifier, VideoIdentifier):
            query = {"media_identifier.media_id": IDToMongo.forward(media_identifier.media_id)}
        else:
            raise ValueError(f"Unsupported media identifier `{media_identifier.media_type.value}`")
        self.delete_all(extra_filter=query)

    def find_best_candidates(
        self,
        candidate_media: SequenceOrSet[MediaIdentifierEntity],
        size: int,
        task_node_id: ID | None = None,
        models_ids: Sequence[ID] | None = None,
        inferred_only: bool = False,
    ) -> tuple[ActiveScoreSuggestionInfo, ...]:
        """
        Given a pool of candidate media identifiers, find the 'best' set (i.e. lowest
        active score) of 'size' elements.

        If the task node is provided, the per-task active score will be considered,
        otherwise the per-project active score is used for comparisons.

        :param candidate_media: Media eligible to be selected
        :param size: Max number of elements to return
        :param task_node_id: Optional, task node whose active scores should be used
        :param models_ids: Optional, if specified the query will prioritize the active
            scores generated with one of the models in the list
        :param inferred_only: If True, exclude the media with a default active score
            (i.e. not updated based on the results of an inference).
        :return: Tuple of at most 'size' elements, where each element is an
            ActiveScoreSuggestionInfo corresponding to the selected media.
            The list is sorted by score (better/lower score first).
        """
        media_identifier_mapper = MediaIdentifierToMongo
        if models_ids is None:
            models_ids = []

        # filter the elements
        match_by_media_clause = {
            "$match": {
                "media_identifier": {
                    "$in": [MediaIdentifierToMongo.forward(identifier) for identifier in set(candidate_media)]
                },
            }
        }
        if task_node_id:
            match_by_task_node_clause = {"$match": {"tasks.task_node_id": IDToMongo.forward(task_node_id)}}
        else:
            match_by_task_node_clause = {"$match": {"tasks.task_node_id": ""}}
        match_model_same_filter = {"tasks.model_id": {"$in": [IDToMongo.forward(model_id) for model_id in models_ids]}}
        match_model_not_same_filter = {
            "tasks.model_id": {"$nin": [IDToMongo.forward(model_id) for model_id in models_ids]}
        }
        match_inferred_clause: dict[str, dict[str, Any]] = {
            "$match": {
                "score": {"$lt": 1.0},
                **(match_model_same_filter if models_ids else {}),
            }
        }
        match_inferred_old_clause: dict[str, dict[str, Any]] = {
            "$match": {"score": {"$lt": 1.0}, **match_model_not_same_filter}
        }
        match_non_inferred_clause = {"$match": {"score": {"$eq": 1.0}}}
        # unwind array-like fields
        unwind_by_tasks_clause = {"$unwind": "$tasks"}
        # sort by score
        sort_by_score_project_level_clause = {"$sort": {"score": 1}}
        sort_by_score_task_level_clause = {"$sort": {"tasks.score": 1}}
        # reduce the output size
        limit_at_size_clause = {"$limit": size}
        sample_size_items_clause = {"$sample": {"size": size}}
        # format the output
        project_score_info_project_level_clause = {
            "$project": {
                "_id": 0,
                "media_identifier": 1,
                "score": 1,
                "models": "$tasks.model_id",  # returns array of ids
            }
        }
        project_score_info_task_level_clause = {
            "$project": {
                "_id": 0,
                "media_identifier": 1,
                "score": "$tasks.score",
                "models": "$tasks.model_id",  # returns id
            }
        }

        if task_node_id is None:  # per-project active learning
            inner_query_inferred = [
                match_inferred_clause,
                sort_by_score_project_level_clause,
                limit_at_size_clause,
                project_score_info_project_level_clause,
            ]
            inner_query_inferred_old = [
                match_inferred_old_clause,
                sort_by_score_project_level_clause,
                limit_at_size_clause,
                project_score_info_project_level_clause,
            ]
        else:  # per-task active learning
            inner_query_inferred = [
                match_inferred_clause,
                unwind_by_tasks_clause,  # tasks is array, so must unwind before sorting
                match_by_task_node_clause,  # filter out the other tasks post-unwinding
                sort_by_score_task_level_clause,
                limit_at_size_clause,
                project_score_info_task_level_clause,
            ]
            inner_query_inferred_old = [
                match_inferred_old_clause,
                unwind_by_tasks_clause,  # tasks is array, so must unwind before sorting
                match_by_task_node_clause,  # filter out the other tasks post-unwinding
                sort_by_score_task_level_clause,
                limit_at_size_clause,
                project_score_info_task_level_clause,
            ]
        inner_query_non_inferred = [
            match_non_inferred_clause,
            # Note: we use 'sample' instead of 'limit' because the former shuffles the
            # result. MongoDB internal sorting is predictable and correlated with the
            # upload order of the media (within groups of items with the same score);
            # without shuffling, the active set could appear biased.
            sample_size_items_clause,
            project_score_info_project_level_clause,
        ]

        facet_queries = {"inferred": inner_query_inferred}
        if models_ids:
            facet_queries.update({"inferred_old": inner_query_inferred_old})
        if not inferred_only:
            facet_queries.update({"non_inferred": inner_query_non_inferred})
        aggr_query: list[dict] = [
            match_by_media_clause,
            {"$facet": facet_queries},
        ]

        try:
            best_scores_container = next(self.aggregate_read(aggr_query))
        except StopIteration:
            return ()
        inferred_docs = best_scores_container.get("inferred", [])
        inferred_old_docs = best_scores_container.get("inferred_old", [])
        non_inferred_docs = best_scores_container.get("non_inferred", [])
        # Note: the concatenation order matters because we pick the first-'size' items
        selectable_docs = inferred_docs + inferred_old_docs + non_inferred_docs
        selected_docs = selectable_docs[:size]
        return tuple(
            ActiveScoreSuggestionInfo(
                media_identifier=media_identifier_mapper.backward(score_doc["media_identifier"]),
                score=score_doc["score"],
                # support both ids and arrays of ids
                models_ids=(
                    tuple(IDToMongo.backward(model_id) for model_id in score_doc["models"])
                    if isinstance(score_doc["models"], list)
                    else (IDToMongo.backward(score_doc["models"]),)
                ),
            )
            for score_doc in selected_docs
        )

    def find_unmapped_candidates(
        self, candidate_media: SequenceOrSet[MediaIdentifierEntity]
    ) -> Iterator[MediaIdentifierEntity]:
        """
        Find the elements that have not been 'mapped' yet, i.e. whose active score
        values are still the default one because the real one has not been computed.
        :param candidate_media: Media eligible to be selected
        :return: Tuple of MediaIdentifierEntity corresponding to the unmapped media
        """
        query = {
            "media_identifier": {
                "$in": [MediaIdentifierToMongo.forward(identifier) for identifier in set(candidate_media)]
            },
            "score": 1.0,
        }
        scores = self.get_all(extra_filter=query)
        for score in scores:
            yield score.media_identifier
