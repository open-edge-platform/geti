# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

"""
Job repository module
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pymongo import DESCENDING, IndexModel
from pymongo.errors import DuplicateKeyError

from model.job import Job, NullJob
from model.job_state import JobState
from model.mapper.job_mapper import JobMapper

from sc_sdk.repos.base.session_repo import QueryAccessMode, SessionBasedRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from pymongo.client_session import ClientSession
    from pymongo.command_cursor import CommandCursor
    from pymongo.cursor import Cursor

    from geti_types import ID, Session


class WorkspaceBasedMicroserviceJobRepo(SessionBasedRepo[Job]):
    """
    Repository to persist job entities in the database.

    :param session: Session object; if not provided, it is loaded through get_session()
    """

    collection_name = "job"

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(collection_name=WorkspaceBasedMicroserviceJobRepo.collection_name, session=session)

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("project_id", DESCENDING)]),
            IndexModel([("type", DESCENDING)]),
            IndexModel([("state_group", DESCENDING)]),
            IndexModel([("state", DESCENDING)]),
            IndexModel([("author", DESCENDING)]),
            IndexModel([("start_time", DESCENDING)]),
            IndexModel([("cancellation_info.is_cancelled", DESCENDING)]),
            IndexModel([("cancellation_info.delete_job", DESCENDING)]),
        ]
        return super_indexes + new_indexes

    @property
    def forward_map(self) -> Callable[[Job], dict]:
        return JobMapper.forward

    @property
    def backward_map(self) -> Callable[[dict], Job]:
        return JobMapper.backward

    @property
    def null_object(self) -> NullJob:
        return NullJob()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=JobMapper, parameter=None)

    def update(
        self,
        job_id: ID,
        update: dict | list[dict],
        array_filters=None,  # noqa: ANN001
        mongodb_session: ClientSession | None = None,
    ) -> bool:
        """
        Updates a job document, doesn't create new document if it's not found by ID
        :param job_id: identifier of a job to be deleted
        :param update: job document update or a list of updates if aggregation pipeline should be used
        :param array_filters: filters for nested arrays updates
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :return: True if the job document is updated, False otherwise
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        query.update({"_id": IDToMongo().forward(job_id)})
        result = self._collection.update_one(
            filter=query,
            update=update,
            array_filters=array_filters,
            upsert=False,
            session=mongodb_session,
        )
        return result.modified_count == 1

    def find_one(
        self,
        job_filter: dict,
        latest: bool = False,
        earliest: bool = False,
        mongodb_session: ClientSession | None = None,
    ) -> dict | None:
        """
        Finds and update a job document atomically

        :param job_filter: job filter
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :return: found document
        """
        if latest and earliest:
            raise ValueError("Parameters 'latest' and 'oldest' cannot be both true")

        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        if job_filter is not None:
            query.update(job_filter)

        if latest:
            sort_criteria = [("_id", -1)]
        elif earliest:
            sort_criteria = [("_id", 1)]
        else:
            sort_criteria = None

        return self._collection.find_one(query, sort=sort_criteria, session=mongodb_session)

    def get_document_by_id(self, id_: ID, mongodb_session: ClientSession | None = None) -> dict | None:
        """
        Get document by ID.

        :param id_: ID of the document to fetch
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :return: Found document, or None in case of no match
        """
        return self.find_one(job_filter={"_id": IDToMongo.forward(id_)}, mongodb_session=mongodb_session)

    def update_many(
        self,
        job_filter: dict,
        update: dict,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Updates job documents according to the filter
        :param job_filter: job filter
        :param update: job document update
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        query.update(job_filter)
        self._collection.update_many(filter=query, update=update, upsert=False, session=mongodb_session)

    def insert_document(self, document: dict, mongodb_session: ClientSession | None = None) -> ID:
        """
        Inserts the input document in the database.
        The operation will result in a failure if duplicates are found on:
        - "key" field for non-cancelled SUBMITTED jobs
        - "key" field for jobs in intermediate states
        - flyte "execution_id" field for jobs in SCHEDULED and further steps

        :param document: Document to insert
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :return: ID of the inserted document
        """
        if "_id" not in document:
            document["_id"] = self.generate_id()
        document["_id"] = IDToMongo.forward(document["_id"])
        preliminary_query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        document.update(preliminary_query)

        query = self._get_document_duplicate_filter(document)
        query.update(preliminary_query)

        # Using "$setOnInsert" will not update existing documents
        result = self._collection.update_one(
            filter=query,
            update={"$setOnInsert": document},
            upsert=True,
            session=mongodb_session,
        )
        if result.upserted_id is None:
            raise DuplicateKeyError("Duplicate detected, cannot insert the document.")
        return IDToMongo.backward(result.upserted_id)

    def _get_document_duplicate_filter(self, document: dict) -> dict:
        """
        Returns a dict query for filtering duplicate jobs.

        :param document: Document to check
        :return: Dict for filtering duplicate jobs
        """
        state = document.get("state", -1)
        cancelled = document.get("cancellation_info", {}).get("is_cancelled", False)
        flyte_execution_id = document.get("executions", {}).get("main", {}).get("execution_id", "")

        filters: list[Any] = [{"_id": document.get("_id")}]
        if state == JobState.SUBMITTED.value and not cancelled:
            filters.append(
                {
                    "key": document.get("key"),
                    "state": JobState.SUBMITTED.value,
                    "cancellation_info.is_cancelled": False,
                },
            )
        if JobState.READY_FOR_SCHEDULING.value <= state < JobState.FINISHED.value:
            filters.append(
                {
                    "key": document.get("key"),
                    "state": {
                        "$gte": JobState.READY_FOR_SCHEDULING.value,
                        "$lt": JobState.FINISHED.value,
                    },
                },
            )
        if flyte_execution_id:
            filters.append(
                {
                    "executions.main.execution_id": flyte_execution_id,
                    "state": {"$gte": JobState.SCHEDULED.value},
                }
            )
        return {"$or": filters}

    def save(
        self,
        instance: Job,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Not implemented.
        This repo doesn't suppose working with a mapper and mapped object, but instead operates with dict directly.

        Please use
        :class:`~microservice.job_repo.WorkspaceBasedMicroserviceJobRepo.insert_document`
        for storing a new job document in collection.
        Please use
        :class:`~microservice.job_repo.WorkspaceBasedMicroserviceJobRepo.update`
        for updating a job document in collection.
        """
        raise NotImplementedError

    def save_many(
        self,
        instances: Sequence[Job],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Not implemented.
        This repo doesn't suppose working with a mapper and mapped object, but instead operates with dict directly.

        Please use
        :class:`~microservice.job_repo.WorkspaceBasedMicroserviceJobRepo.insert_document`
        for storing a new job document in collection.
        Please use
        :class:`~microservice.job_repo.WorkspaceBasedMicroserviceJobRepo.update`
        for updating a job document in collection.
        """
        raise NotImplementedError


class SessionBasedMicroserviceJobRepo(SessionBasedRepo[Job]):
    """
    Repository to persist job entities in the database.

    :param session: Session object; if not provided, it is loaded through get_session()
    """

    collection_name = "job"

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(session=session, collection_name=SessionBasedMicroserviceJobRepo.collection_name)

    @property
    def forward_map(self) -> Callable[[Job], dict]:
        return JobMapper.forward

    @property
    def backward_map(self) -> Callable[[dict], Job]:
        return JobMapper.backward

    @property
    def null_object(self) -> NullJob:
        return NullJob()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=JobMapper, parameter=None)
