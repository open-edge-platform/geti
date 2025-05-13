# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for the PipelineDataset
"""

import logging
from collections.abc import Callable, Sequence

from cachetools import LRUCache, cached
from pymongo.client_session import ClientSession
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor
from pymongo.errors import DuplicateKeyError

from iai_core.entities.dataset_entities import NullPipelineDataset, PipelineDataset, TaskDataset
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.repos import DatasetRepo, TaskNodeRepo
from iai_core.repos.base import DatasetStorageBasedSessionRepo
from iai_core.repos.base.session_repo import QueryAccessMode
from iai_core.repos.mappers.cursor_iterator import CursorIterator
from iai_core.repos.mappers.mongodb_mappers.dataset_entity_mapper import PipelineDatasetToMongo

from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier, Session

logger = logging.getLogger(__name__)


class DuplicatePipelineDatasetException(RuntimeError):
    def __init__(self, dataset_storage_identifier: DatasetStorageIdentifier) -> None:
        super().__init__(f"A PipelineDataset already exists for {dataset_storage_identifier}")


class PipelineDatasetRepo(DatasetStorageBasedSessionRepo[PipelineDataset]):
    """
    This repository is responsible for making
    :class:`PipelineDataset` entities persistent in a database.

    The repository implements the interface
    :class:`~iai_core.entities.interfaces.repo_interface.IRepo`, meaning the repository
    follows the CRUD interface. CRUD stands for Create, Read, Update, Delete.  It uses
    MongoDB to persist the serialized data.

    The :class:`PipelineDatasetRepo` is a singleton class, which makes sure that all
    :class:`PipelineDatasetRepo` instances are the same object.
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="pipeline_dataset_entity",
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def null_object(self) -> NullPipelineDataset:
        return NullPipelineDataset()

    @property
    def forward_map(self) -> Callable[[PipelineDataset], dict]:
        return PipelineDatasetToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], PipelineDataset]:
        return PipelineDatasetToMongo.backward

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=PipelineDatasetToMongo, parameter=None)

    def __get_or_create(self) -> PipelineDataset:
        """
        Get the PipelineDataset from the database, or create and persist it if it does not exist.

        :return: PipelineDataset for this dataset storage
        """
        pipeline_dataset_entity = self.get_one()
        if isinstance(pipeline_dataset_entity, NullPipelineDataset):
            task_datasets: dict[ID, TaskDataset] = {}
            project_identifier = ProjectIdentifier(self.identifier.workspace_id, self.identifier.project_id)
            dataset_repo = DatasetRepo(self.identifier)
            task_node_repo = TaskNodeRepo(project_identifier)
            trainable_task_nodes_ids = list(task_node_repo.get_trainable_task_ids())
            for task_node_id in trainable_task_nodes_ids:
                task_dataset = Dataset(purpose=DatasetPurpose.TEMPORARY_DATASET, id=DatasetRepo.generate_id())
                dataset_repo.save_shallow(task_dataset)
                task_dataset_entity = TaskDataset(
                    task_node_id=task_node_id,
                    dataset_id=task_dataset.id_,
                    dataset_storage_id=self.identifier.dataset_storage_id,
                )
                task_datasets[task_node_id] = task_dataset_entity
            pipeline_dataset_entity = PipelineDataset(
                project_id=self.identifier.project_id,
                task_datasets=task_datasets,
                dataset_storage_id=self.identifier.dataset_storage_id,
            )
            try:
                self.save(pipeline_dataset_entity)
            except DuplicatePipelineDatasetException:
                # A duplicate exception may be raised if two threads attempt to create the entity simultaneously;
                # in this case, delete the dataset that we just saved and fetch the pipeline dataset from the DB
                for created_dataset_id in task_datasets:
                    dataset_repo.delete_by_id(created_dataset_id)
                pipeline_dataset_entity = self.get_one()
                if isinstance(pipeline_dataset_entity, NullPipelineDataset):
                    logger.exception(
                        "Failed to store a new PipelineDataset for %s because one already exists, "
                        "but also failed to retrieve the existing one from the database.",
                        self.identifier,
                    )
                    raise RuntimeError("Cannot find or initialize dataset entity")
        return pipeline_dataset_entity

    @staticmethod
    @cached(cache=LRUCache(maxsize=16))
    def get_or_create(dataset_storage_identifier: DatasetStorageIdentifier) -> PipelineDataset:
        """
        Get the PipelineDataset from the database, or create and persist it if it does not exist.

        This method is cached.

        :param dataset_storage_identifier: Identifier of the dataset storage
        :return: PipelineDataset for this dataset storage
        """
        return PipelineDatasetRepo(dataset_storage_identifier).__get_or_create()

    def save(self, instance: PipelineDataset, mongodb_session: ClientSession | None = None) -> None:
        """
        Save a PipelineDataset to the database.

        Unlike other repos, `PipelineDatasetRepo.save` does not overwrite existing documents with the same id;
        instead it raises an exception in case of double write.

        :param instance: Object to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :raises DuplicatePipelineDatasetException: if a document already exists for the same dataset storage
        """
        if instance.id_ == ID():
            raise ValueError("An ID must be assigned before calling save()")

        doc: dict = self.forward_map(instance)
        doc.update(self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE))
        try:
            self._collection.insert_one(document=doc, session=mongodb_session)
            instance.mark_as_persisted()
        except DuplicateKeyError as err:
            raise DuplicatePipelineDatasetException(self.identifier) from err

    def save_many(self, instances: Sequence[PipelineDataset], mongodb_session: ClientSession | None = None) -> None:
        # By design there is only one pipeline dataset entity per project/DS, so 'save_many' should never be called
        raise NotImplementedError

    def delete_by_id(self, id_: ID) -> bool:
        PipelineDatasetRepo.get_or_create.cache.pop((self.identifier,), None)  # type: ignore
        return super().delete_by_id(id_=id_)

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        PipelineDatasetRepo.get_or_create.cache.pop((self.identifier,), None)  # type: ignore
        return super().delete_all(extra_filter=extra_filter)
