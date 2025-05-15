# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Session-based repo interface"""

import abc
import logging
from collections.abc import Callable, Generator, Sequence
from enum import Enum, auto
from typing import Generic, TypeVar, cast
from uuid import UUID

from bson import ObjectId
from cachetools import cached
from cachetools.keys import hashkey
from pycountry import Subdivision
from pymongo import ASCENDING, DESCENDING, IndexModel, MongoClient, UpdateOne
from pymongo.client_session import ClientSession
from pymongo.collation import Collation
from pymongo.collection import Collection
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core.repos.mappers.cursor_iterator import CursorIterator
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

from .constants import ID_FIELD_NAME, LOCATION_FIELD_NAME, ORGANIZATION_ID_FIELD_NAME, WORKSPACE_ID_FIELD_NAME
from .mongo_connector import MongoConnector
from geti_types import CTX_SESSION_VAR, ID, PersistentEntity, Session, make_session

PersistedEntityT = TypeVar("PersistedEntityT", bound=PersistentEntity)
logger = logging.getLogger(__name__)


class QueryAccessMode(Enum):
    """
    Access mode of a database query (read or write)
    """

    READ = auto()
    WRITE = auto()


class MissingSessionPolicy(Enum):
    """
    Policy to determine the repo behavior when no session information is available
    """

    USE_DEFAULT = auto()
    RAISE_EXCEPTION = auto()


class SessionBasedRepo(Generic[PersistedEntityT], metaclass=abc.ABCMeta):
    """
    Interface for session-based repo.

    :param collection_name: Name of the database collection
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    :param missing_session_policy: Policy to determine the repo behavior when no session information is available
    """

    def __init__(
        self,
        collection_name: str,
        session: Session | None = None,
        missing_session_policy: MissingSessionPolicy = MissingSessionPolicy.RAISE_EXCEPTION,
    ) -> None:
        self._session: Session
        if session is not None:
            self._session = session
            logger.debug(f"{self.__class__.__name__} initialized with session from argument")
        else:
            try:
                self._session = CTX_SESSION_VAR.get()
                logger.debug(f"{self.__class__.__name__} initialized with session from context var")
            except LookupError:
                match missing_session_policy:
                    case MissingSessionPolicy.RAISE_EXCEPTION:
                        logger.exception(f"{self.__class__.__name__} cannot be initialized due to missing session")
                        raise
                    case MissingSessionPolicy.USE_DEFAULT:
                        self._session = make_session()
                        logger.debug(f"{self.__class__.__name__} initialized with default session")
        self._collection_name = collection_name
        # Lazy-load the collection so the repo can be instantiated without MongoDB,
        # to simplify testing; note that MongoDB is of course required to use the repo.
        self.__collection: Collection | None = None

    @staticmethod
    @cached(cache={}, key=lambda collection_name, indexes_getter: hashkey(collection_name))  # noqa: ARG005
    # Note: the cache ensures that this method is only called once (or at least rarely) per collection;
    # even though 'create_indexes' skips already existing indexes, calling it repeatedly would be a waste of time.
    # As an extra optimization, the 'indexes' property is wrapped by a callable so it's evaluated lazily when needed.
    def __build_indexes(collection_name: str, indexes_getter: Callable[[], Sequence[IndexModel]]) -> None:
        collection = MongoConnector.get_collection(collection_name=collection_name)
        collection.create_indexes(indexes_getter())

    @property
    def _mongo_client(self) -> MongoClient:
        return MongoConnector.get_mongo_client()

    @property
    def _collection(self) -> Collection:
        if self.__collection is None:
            self.__collection = MongoConnector.get_collection(collection_name=self._collection_name)
            self.__build_indexes(collection_name=self._collection_name, indexes_getter=lambda: self.indexes)
        return self.__collection

    def get_query_location(self, access_mode: QueryAccessMode) -> Subdivision | None:  # noqa: ARG002
        """
        Determine the 'location' where to perform the query based on organization
        configuration and access mode.

        :param access_mode: READ if the query only requires read access to the
            documents, WRITE if it inserts/updates/deletes documents.
        :return: Location as country Subdivision object, or None if no location should
            be specified in the query
        """
        # on-prem organization: ignore location because all accesses are local
        return None

    def preliminary_query_match_filter(self, access_mode: QueryAccessMode) -> dict[str, str | ObjectId | UUID | dict]:
        """
        Filter that must be applied at the beginning of every MongoDB query based on
        find(), update(), insert(), delete(), count() or similar methods.

        The filter ensures that:
          - only data of a specific organization is selected and processed
          - the query runs with the right scope in the sharded cluster

        The filter matches:
          - organization_id
          - workspace_id
          - location (optional, depends on access mode and session info)

        Derived classes may extend this filter provided that super() is called.
        """
        match_filter: dict[str, str | ObjectId | UUID | dict] = {
            ORGANIZATION_ID_FIELD_NAME: IDToMongo.forward(self._session.organization_id),
            WORKSPACE_ID_FIELD_NAME: IDToMongo.forward(self._session.workspace_id),
        }

        # Location
        location = self.get_query_location(access_mode=access_mode)
        if location is not None:
            match_filter[LOCATION_FIELD_NAME] = location.code

        return match_filter

    def preliminary_aggregation_match_stage(
        self, access_mode: QueryAccessMode
    ) -> dict[str, dict[str, str | ObjectId | UUID | dict]]:
        """
        Filter stage ($match) that must be applied at the beginning of every MongoDB
        aggregation pipeline.

        The stage ensures that:
          - only data of a specific organization is selected and processed
          - the query runs with the right scope in the sharded cluster

        The filter matches:
          - organization_id
          - location (optional, depends on access mode and session info)
        """
        return {"$match": self.preliminary_query_match_filter(access_mode=access_mode)}

    @property
    def indexes(self) -> list[IndexModel]:
        """
        Indexes to be created for the collection of this repo

        :return: Tuple of indexes to create; the sequence should be compatible with
            the input of the Collection.create_indexes method
        """
        index = IndexModel(
            [
                (ORGANIZATION_ID_FIELD_NAME, DESCENDING),
                (WORKSPACE_ID_FIELD_NAME, DESCENDING),
                (ID_FIELD_NAME, ASCENDING),
            ]
        )
        return [index]

    @property
    @abc.abstractmethod
    def forward_map(self) -> Callable[[PersistedEntityT], dict]:
        """Forward mapper callable"""

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

    @staticmethod
    def generate_id() -> ID:
        """
        Generates a unique ID that can be assigned to an entity

        :return: Generated ID
        """
        return ID(ObjectId())

    def save(
        self,
        instance: PersistedEntityT,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Save an entity to the database.

        If a document with the same id already exists, it is overwritten.
        Otherwise, a new document is created.

        Steps:
          1) serialize the entity
          2) inject context
          3) insert to DB
          4) mark the object as persisted

        :param instance: Object to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        if instance.id_ == ID():
            raise ValueError("An ID must be assigned before calling save()")

        # mypy confuses PersistedEntityT with MappableEntityType
        doc: dict = self.forward_map(instance)  # type: ignore
        doc.update(self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE))
        self._collection.update_one(
            {"_id": IDToMongo.forward(instance.id_)},
            {"$set": doc},
            upsert=True,
            session=mongodb_session,
        )
        instance.mark_as_persisted()

    def save_many(
        self,
        instances: Sequence[PersistedEntityT],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Save multiple entities of the same type to the database

        Any existing document with the same id of one of the provided instances will be
        overwritten; a new document is created otherwise.

        Steps:
          1) serialize the entities
          2) inject context
          3) insert to DB in bulk
          4) mark the objects as persisted

        :param instances: Sequence of objects to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        if not instances:  # nothing to save
            return

        if any(instance.id_ == ID() for instance in instances):
            raise ValueError("An ID must be assigned to all objects before calling save_many()")

        # mypy confuses PersistedEntityT with MappableEntityType
        docs: tuple[dict, ...] = tuple(self.forward_map(instance) for instance in instances)  # type: ignore
        query_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        for doc in docs:
            doc.update(query_filter)

        update_operations = [UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True) for doc in docs]
        self._collection.bulk_write(update_operations, session=mongodb_session)

        for instance in instances:
            instance.mark_as_persisted()

    def get_by_id(self, id_: ID) -> PersistedEntityT:
        """
        Get an entity by ID.

        The entity must be visible considering the scope (filters) enforced by the repo.

        :param id_: ID of the entity to fetch
        :return: Found entity, or its null placeholder in case of no match
        """
        if id_ == ID():
            return self.null_object

        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        query["_id"] = IDToMongo.forward(id_)
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
        sort_by: str | None = None,
    ) -> PersistedEntityT:
        """
        Get one entity that matches the base query filter and optionally
        an additional filter provided as input.

        This method is mostly useful if the caller expects the collection to contain
        at most one document (unique) that matches the filter.

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :param latest: If True, return the latest matching item (highest id);
            this parameter cannot be enabled together with 'earliest'
        :param earliest: If True, return the earliest matching item (lowest id);
            this parameter cannot be enabled together with 'latest'
        :param sort_by: Optional, field to sort by
        :return: Found entity, or its null placeholder in case of no match
        """
        if latest and earliest:
            raise ValueError("Parameters 'latest' and 'oldest' cannot be both true")

        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        if extra_filter is not None:
            query.update(extra_filter)

        if latest:
            sort_criteria = [(sort_by, -1)] if sort_by is not None else []
            sort_criteria.append(("_id", -1))
        elif earliest:
            sort_criteria = [(sort_by, 1)] if sort_by is not None else []
            sort_criteria.append(("_id", 1))
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
        Get all the entities matching the base query filter and optionally
        an additional filter provided as input.

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :param sort_info: Optional list specifying how to sort the result
        :return: CursorIterator over the found entities
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        if extra_filter is not None:
            query.update(extra_filter)
        cursor = self._collection.find(query, sort=sort_info)
        return self.cursor_wrapper(cursor)

    def get_all_ids(self, extra_filter: dict | None = None) -> Generator[ID, None, None]:
        """
        Get the IDs of all the entities matching the base query filter and optionally
        an additional filter provided as input.

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :return: Generator over the found IDs
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        if extra_filter is not None:
            query.update(extra_filter)
        cursor = self._collection.find(query, projection={"_id": 1})
        return (IDToMongo.backward(result_id["_id"]) for result_id in cursor)

    def _aggregate(
        self,
        pipeline: list[dict],
        access_mode: QueryAccessMode,
        collation: Collation | None = None,
    ) -> CommandCursor:
        """
        Run an aggregation pipeline.

        This method is used internally to implement aggregate_read and aggregate_write.

        :param pipeline: Aggregation pipeline to execute, as a list of MongoDB stages
        :param access_mode: Type of access (read or write)
        :param collation: Optional, collation to use for string comparison
        :return: pymongo CommandCursor over the result set
        """
        pre_match_stage = self.preliminary_aggregation_match_stage(access_mode=access_mode)
        full_pipeline = [pre_match_stage, *pipeline] if pre_match_stage else pipeline
        return self._collection.aggregate(full_pipeline, allowDiskUse=True, collation=collation)

    def aggregate_read(self, pipeline: list[dict], collation: Collation | None = None) -> CommandCursor:
        """
        Run an aggregation pipeline that only reads data (no updates).

        :param pipeline: Aggregation pipeline to execute, as a list of MongoDB stages
        :param collation: Optional, collation to use for string comparison
        :return: pymongo CommandCursor over the result set
        """
        return self._aggregate(pipeline=pipeline, access_mode=QueryAccessMode.READ, collation=collation)

    def aggregate_write(self, pipeline: list[dict], collation: Collation | None = None) -> CommandCursor:
        """
        Run an aggregation pipeline that updates data in the database.

        :param pipeline: Aggregation pipeline to execute, as a list of MongoDB stages
        :param collation: Optional, collation to use for string comparison
        :return: pymongo CommandCursor over the result set
        """
        return self._aggregate(pipeline=pipeline, access_mode=QueryAccessMode.WRITE, collation=collation)

    def distinct(self, key: str, extra_filter: dict | None = None) -> tuple:
        """
        Get all the distinct (unique) values for the given field across the documents
        that match the base query filter

        Note: because MongoDB returns a list, this method is not memory-friendly when
        the unique output values have high-cardinality.

        :param key: name of the field for which to get the distinct values
        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :return: Tuple containing the unique values for the key
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        if extra_filter is not None:
            query.update(extra_filter)
        return tuple(self._collection.distinct(key=key, filter=query))

    def count(self, extra_filter: dict | None = None) -> int:
        """
        Count how many documents match the base query filter and optionally
        an additional filter provided as input.

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :return: Number of matching documents
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        if extra_filter is not None:
            query.update(extra_filter)
        return self._collection.count_documents(filter=query)

    def delete_by_id(self, id_: ID) -> bool:
        """
        Delete an entity by ID.

        The entity must be visible considering the scope (filters) enforced by the repo.

        :param id_: ID of the entity to delete
        :return: True if any DB document was matched and deleted, False otherwise
        """
        if id_ == ID():
            return False

        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        query["_id"] = IDToMongo.forward(id_)
        result = self._collection.delete_one(query)
        return result.deleted_count > 0

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        """
        Delete all the entities matching the base query filter and optionally
        an additional filter provided as input.

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :return: True if any DB document was matched and deleted, False otherwise
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        if extra_filter is not None:
            query.update(extra_filter)
        result = self._collection.delete_many(query)
        return result.deleted_count > 0

    def exists(self, id_: ID) -> bool:
        """
        Check if a document exists in the collection with the given ID.

        :param id_: ID of the document to check
        :return: True if document exist, False otherwise
        """
        if id_ == ID():
            return False
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        query["_id"] = IDToMongo.forward(id_)
        return self._collection.count_documents(filter=query, limit=1) > 0
