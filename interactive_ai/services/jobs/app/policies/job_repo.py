# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Job repository module
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from model.job import Job, NullJob
from model.mapper.job_mapper import JobMapper

from iai_core.repos.base.session_repo import MissingSessionPolicy, QueryAccessMode, SessionBasedRepo
from iai_core.repos.mappers.cursor_iterator import CursorIterator

if TYPE_CHECKING:
    from collections.abc import Callable

    from pymongo.client_session import ClientSession
    from pymongo.command_cursor import CommandCursor
    from pymongo.cursor import Cursor

    from geti_types import Session


class SessionBasedPolicyJobRepo(SessionBasedRepo[Job]):
    """
    Repository to persist job entities in the database.

    :param session: Session object; if not provided, it is loaded through get_session()
    """

    collection_name = "job"

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(
            session=session,
            collection_name=SessionBasedPolicyJobRepo.collection_name,
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

    def update_many(
        self,
        filter: dict,
        update: dict,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Updates job documents according to the filter
        :param filter: job filter
        :param update: job document update
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        query.update(filter)
        self._collection.update_many(filter=query, update=update, upsert=False, session=mongodb_session)
