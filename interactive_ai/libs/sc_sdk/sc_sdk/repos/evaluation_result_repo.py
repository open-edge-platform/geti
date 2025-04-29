# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the repository for EvaluationResult entities"""

import logging
from collections.abc import Callable, Sequence
from typing import Any
from uuid import UUID

from bson import ObjectId
from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.evaluation_result import EvaluationPurpose, EvaluationResult, NullEvaluationResult
from sc_sdk.entities.metrics import NullPerformance, Performance
from sc_sdk.repos.base import ProjectBasedSessionRepo
from sc_sdk.repos.base.session_repo import QueryAccessMode
from sc_sdk.repos.mappers import CursorIterator, IDToMongo, PerformanceToMongo
from sc_sdk.repos.mappers.mongodb_mappers.evaluation_result_mapper import EvaluationResultToMongo

from geti_types import ID, ProjectIdentifier, Session

logger = logging.getLogger(__name__)


class EvaluationResultRepo(ProjectBasedSessionRepo[EvaluationResult]):
    """
    Repository to persist EvaluationResult entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through get_session()
    """

    collection_name = "evaluation_result"

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
    def forward_map(self) -> Callable[[EvaluationResult], dict]:
        return EvaluationResultToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], EvaluationResult]:
        return EvaluationResultToMongo.backward

    @property
    def null_object(self) -> NullEvaluationResult:
        return NullEvaluationResult()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=EvaluationResultToMongo, parameter=None)

    def preliminary_query_match_filter(self, access_mode: QueryAccessMode) -> dict[str, str | ObjectId | UUID | dict]:
        match_filter = super().preliminary_query_match_filter(access_mode=access_mode)
        if access_mode == QueryAccessMode.READ:
            # Exclude model test results
            match_filter["purpose"] = {"$ne": EvaluationPurpose.MODEL_TEST.name}
        return match_filter

    def get_latest_by_model_ids(
        self, equivalent_model_ids: Sequence[ID], purpose: EvaluationPurpose | None = None
    ) -> EvaluationResult:
        """
        Finds the latest evaluation result that is associated with any given model IDs.
        This method can be used, for example, to retrieve the evaluation result of a group of
        equivalent models (i.e. models that are indistinguishable performance-wise),
        without explicitly knowing to which model the evaluation result belong to.

        :param equivalent_model_ids: Sequence containing the model ID used to generate the evaluation result.
        :param purpose: Optional purpose of the evaluation result to further filter the results. See EvaluationPurpose.
        :return: Latest evaluation result if any, NullEvaluationResult otherwise.
        """
        query = self._get_query_by_model_ids(model_ids=equivalent_model_ids, purpose=purpose)
        return self.get_one(extra_filter=query, latest=True)

    def get_performance_by_model_ids(
        self,
        equivalent_model_ids: Sequence[ID],
        purpose: EvaluationPurpose | None = None,
    ) -> Performance:
        """
        Fetches the model score associated with list of equivalent model IDs, i.e.
        models that are indistinguishable performance-wise.
        The purpose of this method is to make sure the score can be fetched
        without deserializing the entire EvaluationResult.

        :param equivalent_model_ids: Sequence containing the model ID used to generate the evaluation result.
        :param purpose: Optional purpose of the evaluation result to further filter the results. See EvaluationPurpose.
        :return: Latest model performance if any, NullPerformance otherwise.
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        query.update(self._get_query_by_model_ids(model_ids=equivalent_model_ids, purpose=purpose))
        doc: dict | None = self._collection.find_one(query, sort=[("_id", -1)])
        if doc is None:
            return NullPerformance()
        return PerformanceToMongo.backward(doc.get("performance", {}))

    @staticmethod
    def _get_query_by_model_ids(model_ids: Sequence[ID], purpose: EvaluationPurpose | None = None) -> dict:
        """Builds a query for filtering by model IDs and EvaluationPurpose."""
        query: dict[str, Any] = {"model_id": {"$in": [IDToMongo.forward(model_id) for model_id in model_ids]}}
        if purpose is not None:
            query["purpose"] = purpose.name
        return query

    def delete_all_by_model_id(self, model_id: ID) -> None:
        """
        Deletes all evaluation results associated with the given model ID.

        :param model_id: Model ID to filter the evaluation results.
        """
        self.delete_all(extra_filter={"model_id": IDToMongo.forward(model_id)})
