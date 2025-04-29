# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for MediaScore entities
"""

import logging
from collections.abc import Callable, Sequence

import pymongo
from pymongo import IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.media_score import MediaScore, NullMediaScore
from sc_sdk.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo
from sc_sdk.repos.mappers.mongodb_mappers.media_score_mapper import MediaScoreToMongo

from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, Session

logger = logging.getLogger(__name__)


class MediaScoreRepo(DatasetStorageBasedSessionRepo[MediaScore]):
    """
    Repository to persist MediaScore entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    collection_name = "media_score"

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name=MediaScoreRepo.collection_name,
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def forward_map(self) -> Callable[[MediaScore], dict]:
        return MediaScoreToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], MediaScore]:
        return MediaScoreToMongo.backward

    @property
    def null_object(self) -> NullMediaScore:
        return NullMediaScore()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=MediaScoreToMongo, parameter=None)

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("media_identifier", pymongo.DESCENDING)]),
            IndexModel([("media_identifier.media_id", pymongo.DESCENDING)]),
            IndexModel([("model_test_result_id", pymongo.DESCENDING)]),
        ]
        return super_indexes + new_indexes

    def get_by_test_and_media_identifier(
        self, model_test_result_id: ID, media_identifier: MediaIdentifierEntity
    ) -> MediaScore:
        """
        Get a MediaScore instance in model test with given id and media identifier.

        :param model_test_result_id: ID of the test result
        :param media_identifier: Media identifier of the entity to retrieve
        :return: MediaScore instance if found, NullMediaScore otherwise
        """
        query = {
            "model_test_result_id": IDToMongo.forward(model_test_result_id),
            "media_identifier": MediaIdentifierToMongo.forward(media_identifier),
        }
        return self.get_one(extra_filter=query)

    def set_annotated_label_ids_by_test_and_media_identifier(
        self, annotated_label_ids: Sequence[ID], model_test_result_id: ID, media_identifier: MediaIdentifierEntity
    ) -> None:
        """
        Sets the "annotated_label_ids" a MediaScore instance in model test with given id and media identifier.

        :param annotated_label_ids: Annotated label ids to set
        :param model_test_result_id: ID of the test result
        :param media_identifier: Media identifier of the entity to retrieve
        """
        query = {
            "model_test_result_id": IDToMongo.forward(model_test_result_id),
            "media_identifier": MediaIdentifierToMongo.forward(media_identifier),
        }
        result = self._collection.update_one(
            query,
            {"$set": {"annotated_label_ids": [IDToMongo.forward(_id) for _id in annotated_label_ids]}},
            upsert=False,
        )
        if not result.modified_count:
            raise ValueError(
                f"MediaScore not found for model test result {model_test_result_id} and media {media_identifier}"
            )

    def delete_all_by_media_id(self, media_id: ID) -> None:
        """
        Delete MediaScore instances given its media identifier

        :param media_id: Media id
        """
        query = {"media_identifier.media_id": IDToMongo.forward(media_id)}
        self.delete_all(extra_filter=query)

    def delete_all_by_model_test_result_id(self, model_test_result_id: ID) -> None:
        """
        Delete all MediaScore instances given its test result id

        :param model_test_result_id: Test result id
        """
        query = {"model_test_result_id": IDToMongo.forward(model_test_result_id)}
        self.delete_all(extra_filter=query)
