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
This module implements the repository for the AutoTrainActivation
"""

import logging
from collections.abc import Callable, Sequence
from typing import Any

from pymongo import DESCENDING, IndexModel
from pymongo.client_session import ClientSession
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from entities.auto_train_activation import AutoTrainActivation, NullAutoTrainActivation
from storage.mappers.auto_train_activation_mapper import AutoTrainActivationToMongo

from geti_types import ID, ProjectIdentifier, Session
from sc_sdk.repos.base import ProjectBasedSessionRepo
from sc_sdk.repos.base.session_repo import QueryAccessMode
from sc_sdk.repos.mappers import IDToMongo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.services import ModelService

logger = logging.getLogger(__name__)


class ProjectBasedAutoTrainActivationRepo(ProjectBasedSessionRepo[AutoTrainActivation]):
    """
    Repository to persist AutoTrainActivation entities in the database.

    The ID of AutoTrainActivation entities must be the same ID of the task node they refer to.
    This ensures that two documents with different task node ID can never exist together in the collection,
    since the second insertion would raise an exception.
    Note that it is not possible to use unique indexes due to sharding limitations.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="auto_train_activation",
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("ready", DESCENDING)]),
        ]
        return super_indexes + new_indexes

    @property
    def forward_map(self) -> Callable[[AutoTrainActivation], dict]:
        return AutoTrainActivationToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], AutoTrainActivation]:
        return AutoTrainActivationToMongo.backward

    @property
    def null_object(self) -> NullAutoTrainActivation:
        return NullAutoTrainActivation()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor, mapper=AutoTrainActivationToMongo, parameter=None
        )

    def upsert_timestamp_for_task(
        self, instance: AutoTrainActivation, mongodb_session: ClientSession | None = None
    ) -> None:
        """
        Updates the timestamp (`request_time`) of an AutoTrainActivation document if it already exists.
        Otherwise, a new document is created.

        Note: The activation readiness and model_storage_id are not updated, as they may interfere with the
        auto-training deferred request logic.

        :param instance: AutoTrainActivation object to upsert
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        query.update({"_id": IDToMongo().forward(instance.id_)})
        doc = self.forward_map(instance)
        # Remove "ready" and "model_storage_id" fields from the document if present
        doc.pop("ready", None)
        doc.pop("model_storage_id", None)
        self._collection.update_one(
            filter=query,
            update={"$set": doc},
            upsert=True,
            session=mongodb_session,
        )

    def set_auto_train_readiness_by_task_id(
        self,
        task_node_id: ID,
        readiness: bool,
        bypass_debouncer: bool = False,
        raise_exc_on_missing: bool = True,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Updates the readiness of an existing AutoTrainActivation document.

        Note: Auto-training always triggers training on the current active model.

        :param task_node_id: ID of the task node
        :param readiness: True if auto-training is ready to be activated, False otherwise.
        :param bypass_debouncer: If this parameter and 'readiness' are both true, the AutoTrainActivation
            document will be updated to specify that the auto-training request should be processed immediately,
            without applying any debouncing period.
        :param raise_exc_on_missing: If True, raise an exception if no document exists for the task; if False, continue
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :raises ValueError: If 'raise_exc_on_missing' and no AutoTrainActivation document exist for the given task node
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        query["_id"] = IDToMongo.forward(task_node_id)
        update_doc: dict[str, Any] = {"ready": readiness}
        if readiness:
            active_model_storage = ModelService.get_active_model_storage(
                project_identifier=self.identifier, task_node_id=task_node_id
            )
            update_doc["model_storage_id"] = IDToMongo.forward(active_model_storage.id_)
            if bypass_debouncer:
                update_doc["bypass_debouncer"] = True
        result = self._collection.update_one(
            filter=query,
            update={"$set": update_doc},
            upsert=False,
            session=mongodb_session,
        )
        if result.matched_count != 1 and raise_exc_on_missing:
            raise ValueError(
                f"Cannot update AutoTrainActivation document with ID '{task_node_id}' because it does not exist."
            )

    def save(
        self,
        instance: AutoTrainActivation,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        logger.warning("Avoid saving AutoTrainActivation objects directly except for testing purposes.")
        super().save(instance=instance, mongodb_session=mongodb_session)

    def save_many(
        self,
        instances: Sequence[AutoTrainActivation],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        logger.warning("Avoid saving AutoTrainActivation objects directly except for testing purposes.")
        super().save_many(instances=instances, mongodb_session=mongodb_session)
