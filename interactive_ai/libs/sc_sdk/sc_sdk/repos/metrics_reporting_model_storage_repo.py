# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for model storage based metrics
"""

import logging
from collections.abc import Callable
from typing import Any

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.model_storage import ModelStorage, NullModelStorage
from sc_sdk.repos import ModelStorageRepo
from sc_sdk.repos.base.read_only_repo import ReadOnlyRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator

logger = logging.getLogger(__name__)


class MetricsReportingModelStorageRepo(ReadOnlyRepo[ModelStorage]):
    """
    Repository to report metrics based on the project repo.
    """

    collection_name = ModelStorageRepo.collection_name

    def __init__(self) -> None:
        super().__init__(collection_name=MetricsReportingModelStorageRepo.collection_name)

    @property
    def backward_map(self) -> Callable[[dict], ModelStorage]:
        raise NotImplementedError

    @property
    def null_object(self) -> ModelStorage:
        return NullModelStorage()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        raise NotImplementedError

    def get_total_number_of_models_per_arch(self) -> dict[str, int]:
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "model_template_id": {
                        "$nin": ["dataset", "crop"],
                    },
                },
            },
            {
                "$lookup": {
                    "from": "model",
                    "localField": "_id",
                    "foreignField": "model_storage_id",
                    "as": "models",
                    "pipeline": [
                        {
                            "$match": {"model_format": "BASE_FRAMEWORK", "model_status": "SUCCESS"},
                        },
                        {
                            "$project": {
                                "_id": 1,
                            },
                        },
                    ],
                },
            },
            {
                "$group": {
                    "_id": "$model_template_id",
                    "model_count": {
                        "$sum": {
                            "$size": "$models",
                        },
                    },
                },
            },
        ]
        docs = self.aggregate_read(pipeline=pipeline)

        return {doc["_id"]: doc["model_count"] for doc in docs}

    def get_total_number_of_models_per_task_type(self) -> dict[str, int]:
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "model_template_id": {
                        "$nin": ["dataset", "crop"],
                    },
                },
            },
            {
                "$lookup": {
                    "from": "task_node",
                    "localField": "task_node_id",
                    "foreignField": "_id",
                    "as": "task_node",
                    "pipeline": [
                        {
                            "$project": {
                                "_id": 1,
                                "task_type": 1,
                            },
                        },
                    ],
                },
            },
            {
                "$unwind": {
                    "path": "$task_node",
                },
            },
            {
                "$lookup": {
                    "from": "model",
                    "localField": "_id",
                    "foreignField": "model_storage_id",
                    "as": "models",
                    "pipeline": [
                        {
                            "$match": {"model_format": "BASE_FRAMEWORK", "model_status": "SUCCESS"},
                        },
                        {
                            "$project": {
                                "_id": 1,
                            },
                        },
                    ],
                },
            },
            {
                "$group": {
                    "_id": "$model_template_id",
                    "task_type": {
                        "$first": "$task_node.task_type",
                    },
                    "model_count": {
                        "$sum": {
                            "$size": "$models",
                        },
                    },
                },
            },
            {
                "$group": {"_id": "$task_type", "model_count": {"$sum": "$model_count"}},
            },
        ]
        docs = self.aggregate_read(pipeline=pipeline)
        return {doc["_id"]: doc["model_count"] for doc in docs}
