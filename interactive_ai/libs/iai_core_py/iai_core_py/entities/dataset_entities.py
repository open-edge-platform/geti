# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the TaskDataset and PipelineDataset"""

from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.datasets import Dataset
from iai_core_py.entities.persistent_entity import PersistentEntity
from iai_core_py.repos.dataset_repo import DatasetRepo

from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity


class TaskDataset:
    """
    TaskDataset is a persistent entity that is responsible for handling training datasets for a task. This is
    done by making calls to the DatasetRepo. The task and dataset ID are unchanging, but the content of the referenced
    dataset changes as the user annotates or trains. The TaskDataset is not persistent - all task dataset entities
    are saved together in the PipelineDatasetRepo

    :param task_node_id: ID of the task that the dataset entity belongs to
    :param dataset_id: ID of the dataset in the repo
    :param dataset_storage_id: ID of the dataset storage the dataset is saved to
    """

    def __init__(self, task_node_id: ID, dataset_id: ID, dataset_storage_id: ID) -> None:
        self.task_node_id = task_node_id
        self.dataset_id = dataset_id
        self.dataset_storage_id = dataset_storage_id

    def get_dataset(self, dataset_storage: DatasetStorage) -> Dataset:
        """
        Get the dataset from the Repo.

        :param dataset_storage: DatasetStorage the dataset is saved in
        :return: The obtained dataset
        """
        if not dataset_storage.id_ == self.dataset_storage_id:
            raise ValueError(
                f"Cannot use dataset entity for task {self.task_node_id} in combination with "
                f"dataset storage {dataset_storage.id_}: expected dataset storage {self.dataset_id}"
            )
        return DatasetRepo(dataset_storage.identifier).get_by_id(self.dataset_id)

    def get_dataset_items_for_media_identifiers(
        self,
        media_identifiers: list[MediaIdentifierEntity],
        dataset_storage_identifier: DatasetStorageIdentifier,
    ) -> tuple[DatasetItem, ...]:
        """
        For a list of media identifiers, get the dataset items connected to those media identifiers.

        :param media_identifiers: List of MediaIdentifiers for which to find the dataset items from the dataset
        :param dataset_storage_identifier: Identifier of the dataset storage containing the media
        """
        if not media_identifiers:
            return ()
        dataset_repo = DatasetRepo(dataset_storage_identifier)
        return tuple(
            dataset_repo.get_items_by_dataset_and_media_identifiers(
                dataset_id=self.dataset_id, media_identifiers=media_identifiers
            )
        )

    def save_dataset(self, dataset: Dataset, dataset_storage_identifier: DatasetStorageIdentifier) -> None:
        """
        Save an updated version of the dataset to the repo

        :param dataset: Updated instance of the dataset
        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the dataset
        """
        if not dataset_storage_identifier.dataset_storage_id == self.dataset_storage_id:
            raise ValueError(
                f"Cannot use dataset entity for task {self.task_node_id} in combination with "
                f"dataset storage {dataset_storage_identifier}: expected dataset storage {self.dataset_storage_id}"
            )
        if not dataset.id_ == self.dataset_id:
            raise ValueError(
                f"Cannot save dataset with ID {dataset.id_} to the dataset entity: the ID of the task "
                f"dataset must stay the same."
            )
        DatasetRepo(dataset_storage_identifier).save_shallow(dataset)

    def add_dataset(self, new_dataset: Dataset, dataset_storage_identifier: DatasetStorageIdentifier) -> None:
        """
        Add items from a new dataset to the dataset and save it to the repo.

        :param new_dataset: New dataset with items to be added to the dataset
        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the dataset
        """
        items_to_add = list(new_dataset)
        if not items_to_add:
            return
        DatasetRepo(dataset_storage_identifier).add_items_to_dataset(
            dataset_items=items_to_add, dataset_id=self.dataset_id
        )

    def remove_items_for_media(
        self, media_id: ID, dataset_storage_identifier: DatasetStorageIdentifier
    ) -> tuple[ID, ...]:
        """
        Remove all dataset items relative to a media.

        This method is called when a 'media deleted' message is received by the director

        :param media_id: ID of the media to be deleted
        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the dataset
        :return: Tuple containing the IDs of the removed items
        """
        return DatasetRepo(dataset_storage_identifier).delete_items_by_dataset_and_media(
            dataset_id=self.dataset_id, media_id=media_id
        )

    def remove_items_for_media_identifiers(
        self,
        media_identifiers: list[MediaIdentifierEntity],
        dataset_storage_identifier: DatasetStorageIdentifier,
    ) -> tuple[ID, ...]:
        """
        For a list of media identifiers, remove all dataset items connected to those media identifiers. This method
        is used when new annotations are added for a media, so that new dataset items can be created afterward.

        :param media_identifiers: List of MediaIdentifiers for which to remove the datasetitems from the dataset
        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the dataset
        :return: Tuple containing the IDs of the removed items
        """
        if not media_identifiers:
            return ()
        dataset_repo = DatasetRepo(dataset_storage_identifier)
        return dataset_repo.delete_items_by_dataset_and_media_identifiers(
            dataset_id=self.dataset_id, media_identifiers=media_identifiers
        )

    @staticmethod
    def save_subsets(dataset: Dataset, dataset_storage_identifier: DatasetStorageIdentifier) -> None:
        """
        Update the subsets in the current dataset to the subsets in the passed dataset.

        :param dataset: Dataset containing items with new subsets
        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the dataset
        """
        DatasetRepo(dataset_storage_identifier).save_subsets_in_dataset(dataset=dataset)

    def get_latest_annotation_scene_id(self, dataset_storage_identifier: DatasetStorageIdentifier) -> ID:
        """
        Queries the latest annotation scene ID from the items in the dataset

        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the dataset
        :return: ID of the latest annotation scene in the dataset
        """
        return DatasetRepo(dataset_storage_identifier).get_latest_annotation_scene_id(dataset_id=self.dataset_id)

    def __repr__(self) -> str:
        return f"TaskDataset(task_node_id={self.task_node_id}, dataset_id={self.dataset_id})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaskDataset):
            return False
        return self.task_node_id == other.task_node_id and self.dataset_id == other.dataset_id


class PipelineDataset(PersistentEntity):
    """
    The PipelineDataset holds all TaskDatasetEntities in a project. The TaskDatasetEntities handle training
    datasets for each trainable task. The PipelineDataset is persistent in the PipelineDatasetRepo, so that
    the task datasets can be re-obtained after shutting down the app.

    PipelineDataset uses the same ID of the corresponding dataset storage, which makes it
    a per-dataset-storage singleton from the logical point of view.

    :param project_id: Project that the PipelineDataset belongs to
    :param task_datasets: TaskDataset for every trainable task in the project
    :param dataset_storage_id: ID of the dataset storage; also used as id for the PipelineDataset
    :param ephemeral: True if the PipelineDataset instance exists only in
        memory, False if it is backed up by the database
    """

    def __init__(
        self,
        project_id: ID,
        task_datasets: dict[ID, TaskDataset],
        dataset_storage_id: ID,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=dataset_storage_id, ephemeral=ephemeral)
        self.project_id = project_id
        self.task_datasets = task_datasets

    @property
    def dataset_storage_id(self) -> ID:
        """Returns the ID of the corresponding dataset storage."""
        return self.id_

    def __repr__(self) -> str:
        return f"PipelineDataset(project_id={self.project_id})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PipelineDataset):
            return False
        return (
            self.id_ == other.id_ and self.project_id == other.project_id and self.task_datasets == other.task_datasets
        )


class NullTaskDataset(TaskDataset):
    """
    Null entity for the TaskDataset
    """

    def __init__(self) -> None:
        super().__init__(task_node_id=ID(), dataset_id=ID(), dataset_storage_id=ID())

    def __repr__(self) -> str:
        return "NullTaskDataset()"


class NullPipelineDataset(PipelineDataset):
    """
    Null entity for the PipelineDataset
    """

    def __init__(self) -> None:
        super().__init__(project_id=ID(), task_datasets={}, dataset_storage_id=ID(), ephemeral=False)

    def __repr__(self) -> str:
        return "NullPipelineDataset()"
