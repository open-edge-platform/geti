# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Read only repo interface"""

import abc
import logging
from collections.abc import Callable, Generator
from typing import Any, Generic, TypeVar, cast

from pymongo import MongoClient
from pymongo.collation import Collation
from pymongo.collection import Collection
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core.entities.persistent_entity import PersistentEntity
from iai_core.repos.mappers.cursor_iterator import CursorIterator
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

from .mongo_connector import MongoConnector
from geti_types import ID

PersistedEntityT = TypeVar("PersistedEntityT", bound=PersistentEntity)
logger = logging.getLogger(__name__)


class ReadOnlyRepo(Generic[PersistedEntityT], metaclass=abc.ABCMeta):
    """
    Interface for read only repo without a session.

    This repo is intended for metrics

    :param collection_name: Name of the database collection
    """

    def __init__(
        self,
        collection_name: str,
    ) -> None:
        self._collection_name = collection_name
        # Lazy-load the collection so the repo can be instantiated without MongoDB,
        # to simplify testing; note that MongoDB is of course required to use the repo.
        self.__collection: Collection | None = None

    @property
    def _mongo_client(self) -> MongoClient:
        return MongoConnector.get_mongo_client()

    @property
    def _collection(self) -> Collection:
        if self.__collection is None:
            self.__collection = MongoConnector.get_collection(collection_name=self._collection_name)
        return self.__collection

    @property
    @abc.abstractmethod
    def backward_map(self) -> Callable[[dict], PersistedEntityT]:
        """Backward mapper callable"""

    @property
    @abc.abstractmethod
    def null_object(self) -> PersistedEntityT:
        """Return the placeholder for null instance of the class"""

    @property
    @abc.abstractmethod
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        """Return a callable that transforms a pymongo Cursor into a CursorIterator"""

    def get_by_id(self, id_: ID) -> PersistedEntityT:
        """
        Get an entity by ID.

        The entity must be visible considering the scope (filters) enforced by the repo.

        :param id_: ID of the entity to fetch
        :return: Found entity, or its null placeholder in case of no match
        """
        if id_ == ID():
            return self.null_object

        query = {"_id": IDToMongo.forward(id_)}
        doc: dict | None = self._collection.find_one(query)
        if doc is None:
            return self.null_object
        entity = self.backward_map(doc)
        # mypy confuses PersistedEntityT with MappableEntityType
        return cast("PersistedEntityT", entity)

    def get_one(
        self,
        extra_filter: dict | None = None,
        latest: bool = False,
        earliest: bool = False,
    ) -> PersistedEntityT:
        """
        Get one entity that matches the base query filter and optionally
        an additional filter provided as input.

        This method is mostly useful if the caller expects the collection to contain
        at most one document (unique) that matches the filter.

        :param extra_filter: Optional filter to apply
        :param latest: If True, return the latest matching item (highest id);
            this parameter cannot be enabled together with 'earliest'
        :param earliest: If True, return the earliest matching item (lowest id);
            this parameter cannot be enabled together with 'latest'
        :return: Found entity, or its null placeholder in case of no match
        """
        if latest and earliest:
            raise ValueError("Parameters 'latest' and 'oldest' cannot be both true")

        query = {}
        if extra_filter is not None:
            query.update(extra_filter)

        if latest:
            sort_criteria = [("_id", -1)]
        elif earliest:
            sort_criteria = [("_id", 1)]
        else:
            sort_criteria = None

        doc: dict | None = self._collection.find_one(query, sort=sort_criteria)
        if doc is None:
            return self.null_object
        entity = self.backward_map(doc)
        # mypy confuses PersistedEntityT with MappableEntityType
        return cast("PersistedEntityT", entity)

    def get_all(
        self, extra_filter: dict | None = None, sort_info: list | None = None
    ) -> CursorIterator[PersistedEntityT]:
        """
        Get all the entities from the collection and optionally matching
        a filter provided as input.

        :param extra_filter: Optional filter to apply
        :param sort_info: Optional list specifying how to sort the result
        :return: CursorIterator over the found entities
        """
        query = {}
        if extra_filter is not None:
            query.update(extra_filter)
        cursor = self._collection.find(query, sort=sort_info)
        return self.cursor_wrapper(cursor)

    def get_all_ids(self, extra_filter: dict | None = None) -> Generator[ID, None, None]:
        """
        Get the IDs of all the entities in the collection and optionally matching
        a filter provided as input.

        :param extra_filter: Optional filter to apply
        :return: Generator over the found IDs
        """
        query = {}
        if extra_filter is not None:
            query.update(extra_filter)
        cursor = self._collection.find(query, projection={"_id": 1})
        return (IDToMongo.backward(result_id["_id"]) for result_id in cursor)

    def aggregate_read(self, pipeline: list[dict], collation: Collation | None = None) -> CommandCursor:
        """
        Run an aggregation pipeline that only reads data (no updates).

        :param pipeline: Aggregation pipeline to execute, as a list of MongoDB stages
        :param collation: Optional, collation to use for string comparison
        :return: pymongo CommandCursor over the result set
        """
        return self._collection.aggregate(pipeline, allowDiskUse=True, collation=collation)

    def distinct(self, key: str, extra_filter: dict | None = None) -> tuple:
        """
        Get all the distinct (unique) values for the given field across the documents
        in the collection.

        Note: because MongoDB returns a list, this method is not memory-friendly when
        the unique output values have high-cardinality.

        :param key: name of the field for which to get the distinct values
        :param extra_filter: Optional filter to apply
        :return: Tuple containing the unique values for the key
        """
        query = {}
        if extra_filter is not None:
            query.update(extra_filter)
        return tuple(self._collection.distinct(key=key, filter=query))

    def count(self, extra_filter: dict[str, Any] | None = None) -> int:
        """
        Count how many documents match the base query filter and optionally
        an additional filter provided as input.

        :param extra_filter: Optional filter to apply
        :return: Number of matching documents
        """
        query = {}
        if extra_filter is not None:
            query.update(extra_filter)
        return self._collection.count_documents(filter=query)

    def exists(self, id_: ID) -> bool:
        """
        Check if a document exists in the collection with the given ID.

        :param id_: ID of the document to check
        :return: True if document exist, False otherwise
        """
        if id_ == ID():
            return False
        query = {"_id": IDToMongo.forward(id_)}
        return self._collection.count_documents(filter=query, limit=1) > 0
