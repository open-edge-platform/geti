# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the repos for dataset and training revision filtering"""

from collections.abc import Callable

from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import DatasetIdentifier
from iai_core.repos.base.constants import (
    DATASET_ID_FIELD_NAME,
    DATASET_STORAGE_ID_FIELD_NAME,
    ORGANIZATION_ID_FIELD_NAME,
    PROJECT_ID_FIELD_NAME,
    WORKSPACE_ID_FIELD_NAME,
)
from iai_core.repos.base.dataset_based_repo import DatasetBasedSessionRepo
from iai_core.repos.mappers import CursorIterator
from iai_core.repos.mappers.mongodb_mappers.training_revision_mapper import TrainingRevisionToMongo

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
