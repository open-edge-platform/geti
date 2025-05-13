# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import io
import logging
from collections.abc import Callable, Generator, Sequence
from typing import cast
from urllib.parse import quote_plus

import numpy as np
from pymongo import DESCENDING, IndexModel
from pymongo.client_session import ClientSession
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from entities.reference_feature import NullReferenceFeature, ReferenceFeature
from entities.reference_feature_adapter import ReferenceFeatureAdapter
from repos.reference_feature_binary_repo import ReferenceFeatureBinaryRepo
from repos.reference_feature_mapper import ReferenceFeatureToMongo

from geti_types import ID, ProjectIdentifier, Session
from iai_core.repos.base import ProjectBasedSessionRepo
from iai_core.repos.base.session_repo import QueryAccessMode
from iai_core.repos.mappers import CursorIterator, IDToMongo

FILENAME_PREFIX = "vps_reference_feature"

logger = logging.getLogger(__name__)


class ReferenceFeatureRepo(ProjectBasedSessionRepo[ReferenceFeature]):
    """
    Repository to persist ReferenceFeature entities in the database.

    The ID of ReferenceFeature entities must be the same ID of the label, to guarantee per-label uniqueness.

    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="vps_reference_feature",
            session=session,
            project_identifier=project_identifier,
        )
        # binary repo is initialized lazily when needed
        self.__binary_repo: ReferenceFeatureBinaryRepo | None = None

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("task_id", DESCENDING)]),
        ]
        return super_indexes + new_indexes

    @property
    def binary_repo(self) -> ReferenceFeatureBinaryRepo:
        """Binary repo relative to the reference features repo"""
        if self.__binary_repo is None:
            self.__binary_repo = ReferenceFeatureBinaryRepo(self.identifier)
        return self.__binary_repo

    @property
    def forward_map(self) -> Callable[[ReferenceFeature], dict]:
        return ReferenceFeatureToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], ReferenceFeature]:
        return ReferenceFeatureToMongo.backward

    @property
    def null_object(self) -> NullReferenceFeature:
        return NullReferenceFeature()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=ReferenceFeatureToMongo,
            parameter=None,
        )

    def _offload_binary_onto_repo(self, reference_feature: ReferenceFeature) -> None:
        """
        Offload the numpy data of a reference feature onto the binary repo.

        :param reference_feature: reference feature to offload
        """
        # Each reference features will be saved with a unique filename in the binary repo
        filename = quote_plus(f"{FILENAME_PREFIX}.npz")

        buffer = io.BytesIO()
        np.savez(buffer, array=reference_feature.numpy)
        data = buffer.getvalue()

        binary_filename = self.binary_repo.save(
            dst_file_name=filename,
            data_source=cast("bytes", data),
            make_unique=True,
        )

        # Replace the in-memory numpy with an adapter
        reference_feature.reference_feature_adapter = ReferenceFeatureAdapter(
            binary_repo=self.binary_repo, binary_filename=binary_filename
        )
        reference_feature._numpy = None

    def _delete_binaries_by_reference_feature(self, reference_feature: ReferenceFeature) -> None:
        """
        Delete the binary data associated with a reference feature.

        :param reference_feature: reference feature to delete
        """
        if reference_feature.data_binary_filename:
            self.binary_repo.delete_by_filename(reference_feature.data_binary_filename)

    def save(
        self,
        instance: ReferenceFeature,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Save a reference feature to the database and its binary data to the persisted storage.

        :param instance: reference feature to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        try:
            if instance.ephemeral:
                self._offload_binary_onto_repo(instance)
            super().save(instance, mongodb_session=mongodb_session)
        except Exception:
            # In case of error, delete any binary file that was already stored
            logger.exception(
                "Error saving reference features `%s` to `%s`; associated binaries will be removed",
                instance.id_,
                self.identifier,
            )
            self._delete_binaries_by_reference_feature(reference_feature=instance)
            raise

    def save_many(
        self,
        instances: Sequence[ReferenceFeature],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Save multiple reference features to the database and their binary data to the persisted storage.

        :param instances: reference features to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        try:
            for instance in instances:
                if instance.ephemeral:
                    self._offload_binary_onto_repo(instance)
                super().save(instance, mongodb_session=mongodb_session)
        except Exception:
            # In case of error, delete any binary file that was already stored
            logger.exception(
                "Error saving multiple reference features to `%s`; docs and binaries will be removed",
                self.identifier,
            )
            for instance in instances:
                self._delete_binaries_by_reference_feature(reference_feature=instance)
                super().delete_by_id(instance.id_)
            raise

    def delete_by_id(self, id_: ID) -> bool:
        """
        Delete a reference feature by its binary data from the database and storage.

        :param id_: ID of the reference feature to delete
        :return: True if the reference feature was deleted, False otherwise
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        query["_id"] = IDToMongo.forward(id_)
        doc = self._collection.find_one(query)
        if not doc:
            logger.warning(
                "Reference feature document with id '%s' not found, possibly it is already deleted",
                id_,
            )
            return False

        is_deleted: bool = super().delete_by_id(id_)

        if is_deleted:
            # delete vector binaries
            self.binary_repo.delete_by_filename(doc["binary_filename"])

        return is_deleted

    def delete_by_label_id(self, label_id: ID) -> bool:
        """
        Delete the corresponding reference feature associated with a label ID from the database and storage.

        Note: The ID of the reference feature entity is the same as the ID of the label it represents.

        :param label_id: ID of the label associated with the reference feature to delete
        :return: True if the reference feature was deleted, False otherwise
        """
        return self.delete_by_id(label_id)

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        """
        Delete all reference features and their binary data from the database and storage.

        :param extra_filter: Filtering is NOT supported for this repo
        :return: True if any reference feature was deleted, False otherwise
        """
        if extra_filter is not None:
            # Since it's not possible to apply the filter to binary repos,
            # we would need a fallback implementation that deletes matched items
            # one by one, which is much slower of course.
            raise NotImplementedError

        any_item_deleted = super().delete_all()

        if any_item_deleted:
            # Delete vector binary data
            self.binary_repo.delete_all()

        return any_item_deleted

    def delete_all_by_task_id(self, task_id: ID) -> bool:
        """
        Delete reference features and their binary data from the database and storage associated with a task ID.

        :param task_id: ID of the task to filter by
        :return: True if any reference feature was deleted, False otherwise
        """
        any_item_deleted = False
        for label_id in self.get_all_ids_by_task_id(task_id=task_id):
            any_item_deleted = self.delete_by_label_id(label_id) or any_item_deleted
        return any_item_deleted

    def get_all_ids_by_task_id(self, task_id: ID) -> Generator[ID, None, None]:
        """
        Get all reference feature IDs associated with a task ID.

        :param task_id: ID of the task to filter by
        :return: List of reference feature IDs
        """
        query = {"task_id": IDToMongo.forward(task_id)}
        return self.get_all_ids(extra_filter=query)

    def get_all_by_task_id(self, task_id: ID) -> CursorIterator[ReferenceFeature]:
        """
        Get all reference feature associated with a task ID.

        :param task_id: ID of the task to filter by
        :return: List of reference feature
        """
        query = {"task_id": IDToMongo.forward(task_id)}
        return self.get_all(extra_filter=query)
