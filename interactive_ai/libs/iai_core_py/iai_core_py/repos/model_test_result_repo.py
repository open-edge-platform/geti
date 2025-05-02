# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for ModelTestResult entities
"""

import logging
from collections.abc import Callable
from uuid import UUID

from bson import ObjectId
from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core_py.entities.evaluation_result import EvaluationPurpose
from iai_core_py.entities.model_test_result import ModelTestResult, NullModelTestResult
from iai_core_py.repos import EvaluationResultRepo
from iai_core_py.repos.base import ProjectBasedSessionRepo
from iai_core_py.repos.base.session_repo import QueryAccessMode
from iai_core_py.repos.mappers import IDToMongo
from iai_core_py.repos.mappers.cursor_iterator import CursorIterator
from iai_core_py.repos.mappers.mongodb_mappers.model_test_result_mapper import ModelTestResultToMongo

from geti_types import ID, ProjectIdentifier, Session

logger = logging.getLogger(__name__)


class ModelTestResultRepo(ProjectBasedSessionRepo[ModelTestResult]):
    """
    Repository to persist ModelTestResult entities in the database.

    Note: ModelTestResult entities are stored in the same collection as EvaluationResult.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through get_session()
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name=EvaluationResultRepo.collection_name,
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("model_id", DESCENDING), ("purpose", DESCENDING)]),
            IndexModel([("dataset_storage_ids", DESCENDING), ("purpose", DESCENDING)]),
        ]
        return super_indexes + new_indexes

    @property
    def forward_map(self) -> Callable[[ModelTestResult], dict]:
        return ModelTestResultToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], ModelTestResult]:
        return ModelTestResultToMongo.backward

    @property
    def null_object(self) -> NullModelTestResult:
        return NullModelTestResult()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=ModelTestResultToMongo,
            parameter=None,
        )

    def preliminary_query_match_filter(self, access_mode: QueryAccessMode) -> dict[str, str | ObjectId | UUID | dict]:
        match_filter = super().preliminary_query_match_filter(access_mode=access_mode)
        # Only filter model test results
        match_filter["purpose"] = EvaluationPurpose.MODEL_TEST.name
        return match_filter

    def get_all_by_dataset_storage_id(self, dataset_storage_id: ID) -> CursorIterator[ModelTestResult]:
        """
        Get all model test results given a dataset storage ID.

        :param dataset_storage_id: filter only tests with this dataset storage id
        :return: ModelTestResult CursorIterator
        """
        query = {"dataset_storage_ids": IDToMongo.forward(dataset_storage_id)}
        return self.get_all(extra_filter=query)
