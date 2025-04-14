# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the repository to persist UploadOperation entities in the database.
"""

from collections.abc import Callable

from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from entities import NullUploadOperation, UploadOperation
from repos.upload_operation_mapper import UploadOperationToMongo

from geti_types import Session
from sc_sdk.repos.base import SessionBasedRepo
from sc_sdk.repos.mappers import CursorIterator


class UploadOperationRepo(SessionBasedRepo[UploadOperation]):
    """
    Repository to persist UploadOperation entities in the database.

    :param session: Session object; if not provided, it is loaded through get_session()
    """

    collection_name = "upload_operation"

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(collection_name=UploadOperationRepo.collection_name, session=session)

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("upload_id", DESCENDING)]),
        ]
        return super_indexes + new_indexes

    @property
    def forward_map(self) -> Callable[[UploadOperation], dict]:
        return UploadOperationToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], UploadOperation]:
        return UploadOperationToMongo.backward

    @property
    def null_object(self) -> NullUploadOperation:
        return NullUploadOperation()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=UploadOperationToMongo, parameter=None)

    def get_by_upload_id(self, upload_id: str) -> UploadOperation:
        """
        Get upload operation by the ID of its uploaded file.

        :param upload_id: ID of the uploaded file
        :return: upload operation
        """
        query = {"upload_id": upload_id}
        return self.get_one(extra_filter=query)
