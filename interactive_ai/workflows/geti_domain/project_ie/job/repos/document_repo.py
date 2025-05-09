# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Repos to interact to fetch/store documents from/to MongoDB collections"""

import logging
from collections.abc import Callable, Iterable, Iterator

from geti_types import ProjectIdentifier, Session
from iai_core.repos import ProjectRepo
from iai_core.repos.base import ProjectBasedSessionRepo
from iai_core.repos.base.mongo_connector import MongoConnector
from iai_core.repos.base.session_repo import QueryAccessMode
from iai_core.repos.mappers import CursorIterator
from iai_core.utils.iteration import grouper
from pymongo import IndexModel
from pymongo.collection import Collection
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

logger = logging.getLogger(__name__)


class DocumentRepo(ProjectBasedSessionRepo[None]):  # type: ignore[type-var]
    """
    DocumentRepo allows interacting with MongoDB collections to efficiently fetch/store documents relative to a project.

    :param project_identifier: Identifier of the project to import/export
    """

    PROJECTS_COLLECTION = ProjectRepo.collection_name
    # The blacklist is a list of collections that should not be exported or imported
    BLACKLISTED_COLLECTIONS: list[str] = [
        "auto_train_activation",  # pending auto-training requests should not be mirrored in the imported project
        "auto_train_policy",  # deleted collection
        "compiled_dataset_shard",  # unnecessary (intermediate/tmp data)
        "file_metadata",  # unnecessary (intermediate/tmp data)
        "upload_operation",  # unnecessary (intermediate/tmp data)
        "job",  # jobs relative to the original project should not be copied to the imported one
        "operation",  # unnecessary (intermediate/tmp data)
        "code_deployment",  # can be regenerated if required
        "ndr_config",  # deleted collection
        "ndr_hash",  # deleted collection
    ]

    def __init__(
        self,
        project_identifier: ProjectIdentifier,
        session: Session | None = None,
    ) -> None:
        # Note: this special repo interacts with multiple collections instead of a single one
        super().__init__(
            collection_name="NONE",
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def _collection(self) -> Collection:
        raise NotImplementedError("DocumentRepo does not interact with a single collection")

    @property
    def indexes(self) -> list[IndexModel]:
        raise NotImplementedError("DocumentRepo does not create indices on any collection")

    @property
    def forward_map(self) -> Callable[[None], dict]:
        raise NotImplementedError("DocumentRepo does not serialize Python objects")

    @property
    def backward_map(self) -> Callable[[dict], None]:
        raise NotImplementedError("DocumentRepo does not deserialize documents")

    @property
    def null_object(self) -> None:
        raise NotImplementedError("DocumentRepo does not return objects")

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        raise NotImplementedError("DocumentRepo does not iterate over objects")

    def get_collection_names(self) -> tuple[str, ...]:
        """Get the names of all non-blacklisted collections"""
        database = MongoConnector.get_database()
        return tuple(
            collection_name
            for collection_name in database.list_collection_names()
            if collection_name not in self.BLACKLISTED_COLLECTIONS
        )

    def _get_project_document_from_db(self) -> dict:
        """
        Get the document that describes the project itself

        :return: Document from the projects collection
        """
        projects_collection = MongoConnector.get_collection(collection_name=self.PROJECTS_COLLECTION)
        query_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        # this collection has the project id in '_id' instead of 'project_id'
        query_filter["_id"] = query_filter["project_id"]
        del query_filter["project_id"]
        doc: dict | None = projects_collection.find_one(query_filter)
        if doc is None:
            raise RuntimeError(f"No document found for project `{self.identifier.project_id}`")
        return doc

    def _get_all_documents_from_db_collection(self, collection_name: str) -> Iterator[dict]:
        """
        Fetch all the documents relative to the project in a given collection

        :param collection_name: Name of the collection to scan
        :return: Generator over the found documents
        """
        if collection_name == self.PROJECTS_COLLECTION:
            return iter([self._get_project_document_from_db()])
        collection = MongoConnector.get_collection(collection_name=collection_name)
        query_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        return collection.find(query_filter)

    def get_all_documents_from_db_for_collection(self, collection_name: str) -> Iterator[dict]:
        """
        Fetch all the documents relative to the project for the passed collection name

        :param collection_name: Name of the collection to scan
        :return: Generator over the documents found in that collection
        """
        match collection_name:
            case self.PROJECTS_COLLECTION:
                return iter([self._get_project_document_from_db()])
            case _:
                return self._get_all_documents_from_db_collection(collection_name=collection_name)

    def insert_documents_to_db_collection(
        self,
        collection_name: str,
        documents: Iterable[dict],
        insertion_batch_size: int = 100,
    ) -> None:
        """
        Insert one or more documents to a given MongoDB collection

        :param collection_name: Name of the database collection
        :param documents: Stream of documents to insert in the DB
        :param insertion_batch_size: Write documents to the DB in batches of this size,
            to reduce the number of DB queries
        """
        write_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        if collection_name == self.PROJECTS_COLLECTION:
            write_filter.pop("project_id")

        collection = MongoConnector.get_collection(collection_name=collection_name)

        for batch_of_docs in grouper(documents, chunk_size=insertion_batch_size):
            for doc in batch_of_docs:
                doc.update(write_filter)
            collection.insert_many(batch_of_docs)

    def delete_all_documents(self) -> None:
        query_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        if "project_id" not in query_filter:  # extra-safety for this potentially disruptive method
            logger.error("Documents to delete must be filtered by 'project_id'; skipping deletion")

        for collection_name in self.get_collection_names():
            collection = MongoConnector.get_collection(collection_name=collection_name)
            deletion_result = collection.delete_many(filter=query_filter)
            logger.debug(f"Deleted {deletion_result.deleted_count} documents from collection '{collection_name}'")
