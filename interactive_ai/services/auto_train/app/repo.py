# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Repository for auto-train requests"""

from collections.abc import Callable
from datetime import datetime

from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from entities import AutoTrainActivationRequest, NullAutoTrainActivationRequest
from mapper import AutoTrainActivationToMongo

from geti_types import ID
from iai_core_py.repos.base import SessionBasedRepo
from iai_core_py.repos.base.session_repo import MissingSessionPolicy
from iai_core_py.repos.mappers import CursorIterator, DatetimeToMongo, IDToMongo


class SessionBasedAutoTrainActivationRepo(SessionBasedRepo[AutoTrainActivationRequest]):
    def __init__(self) -> None:
        super().__init__(
            collection_name="auto_train_activation", missing_session_policy=MissingSessionPolicy.USE_DEFAULT
        )

    @property
    def forward_map(self) -> Callable[[AutoTrainActivationRequest], dict]:
        raise NotImplementedError("This repo can only read documents, not save them")

    @property
    def backward_map(self) -> Callable[[dict], AutoTrainActivationRequest]:
        return AutoTrainActivationToMongo.backward

    @property
    def null_object(self) -> NullAutoTrainActivationRequest:
        return NullAutoTrainActivationRequest()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=AutoTrainActivationToMongo,
            parameter=None,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [IndexModel([("ready", DESCENDING)])]
        return super_indexes + new_indexes

    def get_one_ready(self, latest_timestamp: datetime) -> AutoTrainActivationRequest:
        """
        Get one activation request that is ready and issued earlier than a given timestamp

        :param latest_timestamp: Requests with a timestamp later than this value will be ignored,
            unless the request has the 'bypass_debouncer' flag set to True
        :return: AutoTrainActivationRequest, or NullAutoTrainActivationRequest if no match
        """
        query: dict = {
            "ready": True,
            "$or": [
                {"bypass_debouncer": True},
                {"request_time": {"$lte": DatetimeToMongo.forward(latest_timestamp)}},
            ],
        }
        doc: dict | None = self._collection.find_one(query)
        if doc is None:
            return self.null_object
        return self.backward_map(doc)

    def delete_by_task_node_id(self, task_node_id: ID) -> None:
        """
        Delete the document (if any) relative to the given task node

        :param task_node_id: ID of the task node
        """
        query: dict = {"_id": IDToMongo.forward(task_node_id)}
        self._collection.delete_one(query)

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        """
        Delete all the documents

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :return: True if any DB document was matched and deleted, False otherwise
        """
        query = extra_filter if extra_filter else {}
        result = self._collection.delete_many(query)
        return result.deleted_count > 0
