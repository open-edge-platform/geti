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

from typing import TYPE_CHECKING

from model.job import Job, NullJob
from model.mapper.job_mapper import JobMapper

from sc_sdk.repos.base import SessionBasedRepo
from sc_sdk.repos.base.session_repo import MissingSessionPolicy, QueryAccessMode
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from pymongo.client_session import ClientSession
    from pymongo.command_cursor import CommandCursor
    from pymongo.cursor import Cursor

    from geti_types import ID, Session


class SessionBasedSchedulerJobRepo(SessionBasedRepo[Job]):
    """
    Repository to persist job entities in the database.

    :param session: Session object; if not provided, it is loaded through get_session()
    """

    collection_name = "job"

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(
            session=session,
            collection_name=SessionBasedSchedulerJobRepo.collection_name,
            missing_session_policy=MissingSessionPolicy.USE_DEFAULT,
        )

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

    def find_one_and_update(
        self,
        job_filter: dict,
        update: dict,
        mongodb_session: ClientSession | None = None,
    ) -> dict:
        """
        Finds and update a job document atomically
        :param job_filter: job filter
        :param update: job document update
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :return: found document (before applied changes)
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        query.update(job_filter)
        return self._collection.find_one_and_update(filter=query, update=update, upsert=False, session=mongodb_session)

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        if not extra_filter:
            raise ValueError("Empty filter: jobs to delete must be explicitly selected")
        return super().delete_all(extra_filter=extra_filter)

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

    def save(
        self,
        instance: Job,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Not implemented.
        """
        raise NotImplementedError

    def save_many(
        self,
        instances: Sequence[Job],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Not implemented.
        """
        raise NotImplementedError
