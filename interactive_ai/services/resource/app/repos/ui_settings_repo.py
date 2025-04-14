# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the repository for UISettings
"""

from collections.abc import Callable

import pymongo
from pymongo import IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from entities.ui_settings import NullUISettings, UISettings
from repos.ui_settings_mapper import UISettingsToMongo

from geti_types import ID, Session
from sc_sdk.repos.base import SessionBasedRepo
from sc_sdk.repos.base.session_repo import MissingSessionPolicy
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class UISettingsRepo(SessionBasedRepo[UISettings]):
    """
    Repository to persist UISettings entities in the database.

    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(
            collection_name="ui_settings", session=session, missing_session_policy=MissingSessionPolicy.USE_DEFAULT
        )

    @property
    def null_object(self) -> NullUISettings:
        return NullUISettings()

    @property
    def forward_map(self) -> Callable[[UISettings], dict]:
        return UISettingsToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], UISettings]:
        return UISettingsToMongo.backward

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=UISettingsToMongo, parameter=None)

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("user_id", pymongo.DESCENDING)]),
            IndexModel([("project_id", pymongo.DESCENDING)]),
        ]
        return super_indexes + new_indexes

    def get_by_user_id_and_project(self, user_id: str, project_id: ID) -> UISettings:
        """
        Retrieve settings at user and project level.
        """
        query = {"project_id": IDToMongo.forward(project_id), "user_id": user_id}
        return self.get_one(extra_filter=query)

    def get_by_user_id_only(self, user_id: str) -> UISettings:
        """
        Retrieve user level settings, where project_id is not defined.
        """
        query = {"user_id": user_id, "project_id": {"$exists": False}}
        return self.get_one(extra_filter=query)

    def delete_all_by_project_id(self, project_id: ID) -> None:
        """
        Deletes all UISetting entities relative to the project.
        """
        query = {"project_id": IDToMongo.forward(project_id)}
        self.delete_all(extra_filter=query)
