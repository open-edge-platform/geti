# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the MongoDB repos for active suggestion entity"""

from collections.abc import Callable
from typing import Any

from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from active_learning.entities import ActiveSuggestion, NullActiveSuggestion
from active_learning.storage.mappers.mongodb import ActiveSuggestionToMongo

from geti_types import (
    DatasetStorageIdentifier,
    ImageIdentifier,
    MediaIdentifierEntity,
    Session,
    VideoFrameIdentifier,
    VideoIdentifier,
)
from iai_core_py.repos.base import DatasetStorageBasedSessionRepo
from iai_core_py.repos.mappers.cursor_iterator import CursorIterator
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo


class ActiveSuggestionRepo(DatasetStorageBasedSessionRepo[ActiveSuggestion]):
    """
    Repository to persist ActiveSuggestion entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="active_suggestion",
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def forward_map(self) -> Callable[[ActiveSuggestion], dict]:
        return ActiveSuggestionToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], ActiveSuggestion]:
        return ActiveSuggestionToMongo.backward

    @property
    def null_object(self) -> NullActiveSuggestion:
        return NullActiveSuggestion()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=ActiveSuggestionToMongo, parameter=None)

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [IndexModel([("media_identifier", DESCENDING)])]
        return super_indexes + new_indexes

    def get_by_media_identifier(self, media_identifier: MediaIdentifierEntity) -> ActiveSuggestion:
        """
        Get an ActiveSuggestion entity by media identifier.

        :param media_identifier: Media identifier
        :return: ActiveSuggestion if found, else NullActiveSuggestion
        """
        media_filter = {"media_identifier": MediaIdentifierToMongo.forward(media_identifier)}
        return self.get_one(extra_filter=media_filter)

    def get_all_media_identifiers(self) -> tuple[MediaIdentifierEntity, ...]:
        """
        Get all the distinct media identifiers that have been suggested.

        :return: Tuple of suggested media identifiers
        """
        media_identifiers = self.distinct("media_identifier")
        return tuple(MediaIdentifierToMongo.backward(media_identifier) for media_identifier in media_identifiers)

    def delete_by_media_identifier(self, media_identifier: MediaIdentifierEntity) -> None:
        """
        Delete an ActiveSuggestion entity by media identifier.

        :param media_identifier: Media identifier
        """
        media_filter: dict[str, Any]
        if isinstance(media_identifier, ImageIdentifier | VideoFrameIdentifier):
            media_filter = {"media_identifier": MediaIdentifierToMongo.forward(media_identifier)}
        elif isinstance(media_identifier, VideoIdentifier):
            media_filter = {"media_identifier.media_id": IDToMongo.forward(media_identifier.media_id)}
        else:
            raise ValueError(f"Unsupported media identifier `{media_identifier.media_type}`")

        self.delete_all(extra_filter=media_filter)
