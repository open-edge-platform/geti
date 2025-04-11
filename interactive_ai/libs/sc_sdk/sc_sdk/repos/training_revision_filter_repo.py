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

"""This module implements the repos for dataset and training revision filtering"""

from collections.abc import Callable

from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import DatasetIdentifier
from sc_sdk.repos.base.constants import (
    DATASET_ID_FIELD_NAME,
    DATASET_STORAGE_ID_FIELD_NAME,
    ORGANIZATION_ID_FIELD_NAME,
    PROJECT_ID_FIELD_NAME,
    WORKSPACE_ID_FIELD_NAME,
)
from sc_sdk.repos.base.dataset_based_repo import DatasetBasedSessionRepo
from sc_sdk.repos.mappers import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.training_revision_mapper import TrainingRevisionToMongo

from geti_types import Session


class _TrainingRevisionFilterRepo(DatasetBasedSessionRepo[DatasetItem]):
    """
    Repository to store training revision filtering data
    """

    collection_name = "training_revision_filter"

    def __init__(
        self,
        dataset_identifier: DatasetIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name=self.collection_name,
            session=session,
            dataset_identifier=dataset_identifier,
        )

    @property
    def forward_map(self) -> Callable[[DatasetItem], dict]:
        return TrainingRevisionToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], DatasetItem]:
        raise NotImplementedError

    @property
    def null_object(self) -> DatasetItem:
        raise NotImplementedError  # type: ignore[override]

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        raise NotImplementedError

    @property
    def indexes(self) -> list[IndexModel]:
        return [
            IndexModel(
                [
                    (ORGANIZATION_ID_FIELD_NAME, DESCENDING),
                    (WORKSPACE_ID_FIELD_NAME, DESCENDING),
                    (PROJECT_ID_FIELD_NAME, DESCENDING),
                    (DATASET_STORAGE_ID_FIELD_NAME, DESCENDING),
                    (DATASET_ID_FIELD_NAME, DESCENDING),
                    ("subset", DESCENDING),
                ]
            ),  # Indexed due to default UI view using subset filter
        ]
