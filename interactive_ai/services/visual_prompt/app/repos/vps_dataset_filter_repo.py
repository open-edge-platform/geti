# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import functools
import inspect
import logging
import re
from collections.abc import Callable, Generator
from dataclasses import dataclass
from uuid import UUID

from bson import ObjectId

from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier, Session
from iai_core.repos.base.constants import DATASET_STORAGE_ID_FIELD_NAME
from iai_core.repos.base.session_repo import QueryAccessMode
from iai_core.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from iai_core.repos.mappers import IDToMongo

logger = logging.getLogger(__name__)


@dataclass
class VPSSamplingResult:
    """
    Result of sampling annotations by label IDs.

    :param dataset_storage_identifier: identifier of the dataset storage containing the sampled annotation scene
    :param annotation_scene_id: ID of the sampled annotation scene
    :param label_ids: list of label IDs contained in the sampled annotation scene
    """

    dataset_storage_identifier: DatasetStorageIdentifier
    annotation_scene_id: ID
    label_ids: list[ID]


class VPSDatasetFilterRepo(DatasetStorageFilterRepo):
    """
    Project-based version of :class:`~iai_core.repos.data_storage_filter_repo.DataStorageFilterRepo`.
    It is used by the visual prompt service to sample annotation scenes for one-shot learning.

    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    :param project_identifier: Identifier of the project
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        # Set the dataset storage ID to NULL, as we only need to filter by project-based data
        null_dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project_identifier.workspace_id,
            project_id=project_identifier.project_id,
            dataset_storage_id=ID(),
        )
        super().__init__(
            session=session,
            dataset_storage_identifier=null_dataset_storage_identifier,
        )
        self._disable_write_methods()

    def _disable_write_methods(self) -> None:
        """Disable write operations for the repository based on keywords."""
        write_keywords = re.compile("|".join(["write", "delete", "update", "upsert", "save"]))
        superclass = self.__class__.__bases__[0]
        for name, func in inspect.getmembers(superclass, inspect.isfunction):
            # Disable public methods if their names contain keywords associated with write operations
            if write_keywords.search(name) and not name.startswith("_"):
                setattr(self.__class__, name, self._disable_method_decorator(func))

    def _disable_method_decorator(self, func: Callable) -> Callable:
        """Decorator for all write operations to raise an error if called."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> None:  # noqa: ARG001
            logger.warning(
                "VPSDatesetFilterRepo does not support write operation: `%s`",
                func.__name__,
            )
            raise NotImplementedError("This repository is read-only and does not permit any write operations.")

        return wrapper

    def preliminary_query_match_filter(self, access_mode: QueryAccessMode) -> dict[str, str | ObjectId | UUID | dict]:
        """
        Filter that must be applied at the beginning of every MongoDB query based on
        find(), update(), insert(), delete(), count() or similar methods.

        The filter ensures that:
          - only data of a specific organization is selected and processed
          - the query runs with the right scope in the sharded cluster

        The filter matches:
          - organization_id
          - location (optional, depends on access mode and session info)
          - workspace_id
          - project_id

        Derived classes may extend this filter provided that super() is called.
        """
        # Modify the filter query to exclude the dataset storage ID
        match_filter = super().preliminary_query_match_filter(access_mode=access_mode)
        match_filter.pop(DATASET_STORAGE_ID_FIELD_NAME)
        return match_filter

    def sample_annotations_by_label_ids(
        self, label_ids: list[ID], dataset_storage_id: ID | None = None
    ) -> Generator[VPSSamplingResult, None, None]:
        """
        Sample annotation scenes to minimize the number of images required for one-shot learning of the target labels.

        :param label_ids: List of target label IDs to sample annotations for
        :param dataset_storage_id: Optional, if provided only annotation from the specified dataset storage are sampled
        :return: Generator of annotation sampling results
        """
        pipeline: list[dict] = []
        if dataset_storage_id is not None:
            pipeline.append({"$match": {"dataset_storage_id": IDToMongo.forward(dataset_storage_id)}})
        pipeline.extend(
            [
                {
                    "$match": {
                        "label_ids": {"$in": [IDToMongo.forward(label_id) for label_id in label_ids]},
                    },
                },
                {
                    "$project": {
                        "num_labels": {"$size": "$label_ids"},
                        "annotation_scene_id": 1,
                        "dataset_storage_id": 1,
                        "label_ids": 1,
                    }
                },
                {
                    "$addFields": {
                        "label_id": "$label_ids",
                    },
                },
                {"$unwind": {"path": "$label_id"}},
                {"$sort": {"num_labels": -1, "annotation_scene_id": -1}},
                {
                    "$group": {
                        "_id": "$label_id",
                        "max_num_labels": {"$max": "$num_labels"},
                        "doc_with_max_num_labels": {"$first": "$$ROOT"},
                    }
                },
            ]
        )
        result_docs = self.aggregate_read(pipeline=pipeline)
        target_labels = set(label_ids)
        sampled_labels: set[ID] = set()
        for doc in result_docs:
            found_label_ids = [IDToMongo.backward(obj_id) for obj_id in doc["doc_with_max_num_labels"]["label_ids"]]
            unseen_label_ids = (set(found_label_ids) - sampled_labels) & target_labels
            if not unseen_label_ids:
                continue
            if len(sampled_labels) == len(target_labels):
                return  # No more unseen labels to sample
            sampled_labels.update(unseen_label_ids)
            yield VPSSamplingResult(
                dataset_storage_identifier=DatasetStorageIdentifier(
                    workspace_id=self.identifier.workspace_id,
                    project_id=self.identifier.project_id,
                    dataset_storage_id=IDToMongo.backward(doc["doc_with_max_num_labels"]["dataset_storage_id"]),
                ),
                annotation_scene_id=IDToMongo.backward(doc["doc_with_max_num_labels"]["annotation_scene_id"]),
                label_ids=found_label_ids,
            )
