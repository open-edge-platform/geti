# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

"""This module implements the Dataset entity"""

import collections
import datetime
import itertools
import logging
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import overload

import numpy as np

from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.interfaces.dataset_adapter_interface import DatasetAdapterInterface
from sc_sdk.entities.persistent_entity import PersistentEntity
from sc_sdk.entities.subset import Subset
from sc_sdk.utils.time_utils import now
from sc_sdk.utils.uid_generator import generate_uid

from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, VideoFrameIdentifier

logger = logging.getLogger(__name__)


class DatasetPurpose(Enum):
    """Describes the purpose for the dataset.

    This makes it possible to identify datasets for a particular use.
    """

    #: used for user inference.
    # Prediction will generate AnnotationSceneKind.PREDICTION
    INFERENCE = 0
    #: used for training.
    # AnnotationScene contains user annotation of type AnnotationSceneKind.ANNOTATION
    TRAINING = 1
    #: used for pre-evaluation, evaluation, or testing.
    # Prediction will generate AnnotationSceneKind.EVALUATION
    EVALUATION = 2
    #: used for generating output stage.
    # Prediction will generate AnnotationSceneKind.PREDICTION
    GENERATING_OUTPUT = 3
    #: used for dataset slices which are used for analysis.
    # Prediction will generate AnnotationSceneKind.INTERMEDIATE
    TEMPORARY_DATASET = 4
    #: used for task analysis.
    # Prediction will generate AnnotationSceneKind.TASK_PREDICTION
    TASK_INFERENCE = 5

    def __str__(self):
        """Returns the dataset purpose as string."""
        return str(self.name)


class DatasetIterator(collections.abc.Iterator):
    """This DatasetIterator iterates over the dataset lazily.

    Implements collections.abc.Iterator.

    Args:
        dataset (Dataset): Dataset to iterate over.
    """

    def __init__(self, dataset: "Dataset"):
        self.dataset = dataset
        self.index = 0

    def __next__(self) -> DatasetItem:
        """Returns the next dataset item.

        Raises:
            StopIteration: if the end of the dataset is reached.

        Returns:
            DatasetItem: Dataset item.
        """
        if self.index >= len(self.dataset):
            raise StopIteration
        item = self.dataset[self.index]
        self.index += 1
        return item


class Dataset(PersistentEntity):
    """
    A dataset in SC consists of an ID, a list of DatasetItem, a purpose and a creation date.

    .. figure::  /images/object_detection_classification.png
       :align:   center
       :width: 600pt

       Task chain of object detection + crop + Classification

    The Dataset entity can be instantiated in two ways.
    With dataset items, or with a dataset adapter.
    Please mind that the Dataset entity can not be instantiated with both.

    .. rubric:: With dataset items

    This way assumes the dataset item entities are constructed before the Dataset entity is made.

    >>> from sc_sdk.entities.image import Image
    >>> from sc_sdk.entities.annotation import AnnotationScene
    >>> image = Image(...)
    >>> annotation = AnnotationScene(...)
    >>> item_1 = DatasetItem(media=image, annotation_scene=annotation)
    >>> dataset = Dataset(items=[item_1])

    .. rubric:: With a dataset adapter

    Instead of providing the items directly, the Dataset entity can also be instantiated with an adapter.
    The adapter provides the tools to fetch the DatasetItems lazily.

    >>> from sc_sdk.adapters.dataset_adapter import DatasetAdapter
    >>> adapter = DatasetAdapter(...)
    >>> dataset = Dataset(dataset_adapter=adapter)

    ## Iterate over dataset

        Regardless of the instantiation method chosen, the Dataset will work the same.
        The dataset can be iterated:

        >>> dataset = Dataset(items=[item_1])
        >>> for dataset_item in dataset:
        ...     print(dataset_item)
        DatasetItem(
            media=Image(image.jpg, width=640, height=480),
            annotation_scene=NullAnnotationScene(),
            roi=Annotation(
                shape=Rectangle(
                    x=0.0,
                    y=0.0,
                    width=1.0,
                    height=1.0
                    ),
                    labels=[],
                    id=6149e454893b7ebbe3a8faf6
                ),
            subset=NONE
        )

        A particular item can also be fetched:

        >>> first_item = dataset[0]

        Or a slice:

        >>> first_ten = dataset[:10]
        >>> last_ten = dataset[-10:]

    ## Get a subset of Dataset

        To get the test data for validating the network:

        >>> dataset = Dataset()
        >>> testing_subset = dataset.get_subset(Subset.TESTING)

        This subset is also a Dataset. The entities in the subset dataset refer to the same entities as
        in the original dataset. Altering one of the objects in the subset, will also alter them in the original.

    :param items: [Option 1] A list of dataset items to create dataset with
    :param dataset_adapter: [Option 2] An adapter for the Dataset to fetch its entities lazily
    :param purpose: Purpose for dataset. Refer to :class:`DatasetPurpose` for more info.
    :param creation_date: [Optional] Set the creation date of the dataset.
        If None, the datetime will be automatically set to the timestamp of instantiating the entity.
    :param id: ID of dataset
    :param mutable: Default True, set to False if this dataset may not be changed after creation.
    :label_schema_id: ID of the LabelSchema used by the element of this dataset.
        This field is only useful for bookkeeping purposes on dataset used for training/evaluation.
        It is not required for provisional or unannotated dataset.
    """

    def __init__(  # noqa: PLR0913
        self,
        id: ID,
        items: list[DatasetItem] | None = None,
        dataset_adapter: DatasetAdapterInterface | None = None,
        purpose: DatasetPurpose = DatasetPurpose.INFERENCE,
        creation_date: datetime.datetime | None = None,
        mutable: bool = True,
        label_schema_id: ID | None = None,
        ephemeral: bool = True,
    ) -> None:
        if not label_schema_id and purpose in (
            DatasetPurpose.TRAINING,
            DatasetPurpose.EVALUATION,
        ):
            err_msg = (
                f"Attempted to instantiate a Dataset with id {id} and "
                f"with purpose {purpose} without providing a label schema."
            )
            logger.error(err_msg)
            raise ValueError(err_msg)

        PersistentEntity.__init__(self, id_=id, ephemeral=ephemeral)

        self._items: list[DatasetItem] = [] if items is None else items
        self._label_schema_id: ID = ID() if label_schema_id is None else label_schema_id
        self.creation_date = now() if creation_date is None else creation_date
        self.mutable = mutable
        self.dataset_adapter = dataset_adapter
        self.purpose = purpose

    @property
    def label_schema_id(self) -> ID:
        """
        Returns the ID of the label schema relative to the dataset (if any).
        """
        return self._label_schema_id

    @property
    def __items(self) -> list[DatasetItem]:
        if self.dataset_adapter is not None:
            return self.dataset_adapter.get_items()
        return self._items

    @__items.setter
    def __items(self, value: list[DatasetItem]):
        if self.dataset_adapter is not None:
            self.dataset_adapter = None
        self._items = value

    def _fetch(self, key: int | slice | list):
        """
        Fetch the given entity from the self-stored items, or from the adapter.
        Helper function for __getitem__

        :param key: Key called on the dataset. E.g. int (dataset[0]) or slice (dataset[5:9])

        :return: List of DatasetItem or a single DatasetItem.
        """
        # Allow index or slice as input
        if self.dataset_adapter is not None:
            return self.dataset_adapter.fetch(key)

        if isinstance(key, list):
            return [self._fetch(ii) for ii in key]
        if isinstance(key, slice):
            # Get the start, stop, and step from the slice
            return [self._fetch(ii) for ii in range(*key.indices(len(self._items)))]
        if isinstance(key, int | np.int32 | np.int64):
            if key < 0:  # Handle negative indices
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError(f"The index {key} is out of range.")

            if key >= len(self._items):
                raise IndexError("Index out of range for dataset")
            return self._items[key]
        raise TypeError(
            f"Instance of type `{type(key).__name__}` cannot be used to access Dataset items. "
            f"Only slice and int are supported"
        )

    @staticmethod
    def __add_dataset_items(
        dataset1: "Dataset | Sequence[DatasetItem]",
        dataset2: "Dataset | Sequence[DatasetItem]",
        validate_input_schemas: bool = False,
    ) -> list[DatasetItem]:
        """
        Common logic for the methods that add two datasets.
        Given two datasets, it merges them into a single list of items.

        :param dataset1: First Dataset or sequence of DatasetItem
        :param dataset2: Second Dataset or sequence of DatasetItem
        :param validate_input_schemas: Flag to enable a validation check on the label schemas of the inputs.
            If enabled and the two schemas are both non-null datasets and different, an error will be raised
        :return: List of DatasetItem obtained merging the two input datasets
        :raises: ValueError if the inputs' schemas are not null and mismatching
        """
        # Prevent the addition of dataset with explicitly different schemas
        if validate_input_schemas and (
            isinstance(dataset1, Dataset)
            and isinstance(dataset2, Dataset)
            and dataset1.label_schema_id != dataset2.label_schema_id
        ):
            raise ValueError(
                f"Cannot add Datasets relative to different label schemas "
                f"({dataset1.label_schema_id}, {dataset2.label_schema_id})"
            )

        out_datasets: list[list[DatasetItem]] = []
        for in_dataset in (dataset1, dataset2):
            if isinstance(in_dataset, Dataset):
                out_datasets.append(list(in_dataset))
            elif isinstance(in_dataset, Sequence):
                out_datasets.append([item for item in in_dataset if isinstance(item, DatasetItem)])
            else:
                raise ValueError(f"Unrecognized type '{type(in_dataset)}' in dataset addition")
        return out_datasets[0] + out_datasets[1]

    def __repr__(self) -> str:
        return (
            f"Dataset(id_={self.id_}, size={len(self)}, label_schema_id={self.label_schema_id}, mutable={self.mutable})"
        )

    def __len__(self) -> int:
        if self.dataset_adapter is not None:
            return self.dataset_adapter.get_length()
        return len(self.__items)

    def __eq__(self, other: object) -> bool:
        """
        Checks whether the dataset is equal to the operand.
        The computation of equality is:

        - if both datasets are saved, the ID's are compared
        - if either one is not saved, the contents of the datasets are compared.

        :param other: the dataset operand to the equal operator
        :return: True if the datasets are equal
        """
        if not isinstance(other, Dataset):
            return False
        if len(self) == len(other) and self.label_schema_id == other.label_schema_id and self.purpose == other.purpose:
            if other.id_ != ID() and self.id_ != ID():
                return self.id_ == other.id_
            return False not in [self[i] == other[i] for i in range(len(self))]

        return False

    def __add__(self, other: "Dataset | Sequence[DatasetItem]"):
        """
        Returns a new dataset which contains the items from this dataset (self) and the one passed by argument.

        Note that additional info of the dataset might be incoherent to the addition operands.
        In particular, most of the metadata (purpose, schema id, ...) is copied from the first addend.

        :param other: Dataset to add to this object
        :raises: ValueError if the inputs' schemas are not null and mismatching
        :return: New dataset containing the items from both input datasets
        """
        # Merge the items
        items = Dataset.__add_dataset_items(self, other, validate_input_schemas=True)

        return Dataset(
            items=items,
            purpose=self.purpose,
            label_schema_id=self.label_schema_id,
            id=generate_uid(),
        )

    @overload
    def __getitem__(self, key: int) -> DatasetItem: ...

    @overload
    def __getitem__(self, key: slice) -> list[DatasetItem]: ...

    def __getitem__(self, key: slice | int) -> list[DatasetItem] | DatasetItem:
        """
        Return a DatasetItem or a list of DatasetItem, given a slice or an integer.

        Example:
            Given an integer index:

            >>> dataset = Dataset(items=[...])
            >>> first_item = dataset[0]

            Or a slice:

            >>> first_ten = dataset[0:9]
            >>> last_ten = dataset[-9:]

        :param key (Union[slice, int]): key to fetch. Should be `slice` or `int`
        :return: Union["DatasetItem", List["DatasetItem"]]: List of DatasetItem or single DatasetItem
        """
        return self._fetch(key)

    def __iter__(self) -> Iterator[DatasetItem]:
        """
        Return an iterator for the Dataset.
        This iterator is able to iterate over the Dataset lazily.

        :return: DatasetIterator instance
        """
        return DatasetIterator(self)

    def __copy__(self):
        """
        Shallow copy the dataset entity

        :return: The copied dataset
        """
        return Dataset(
            items=self.__items.copy(),
            purpose=self.purpose,
            id=self.id_,
            mutable=self.mutable,
            label_schema_id=self.label_schema_id,
        )

    def get_subset(self, subset: Subset) -> "Dataset":
        # Create a copy of the items (with new ID) so they are not taken away
        # from the original dataset when saving the new dataset.
        items_copy: list[DatasetItem] = []
        for item in self.__items:
            if item.subset == subset:
                # note: it is important that the annotation scene object in memory is
                # the same as in the original item because of the mapper cache.
                item_copy = DatasetItem(
                    id_=generate_uid(),
                    media=item.media,
                    annotation_scene=item.annotation_scene,
                    roi=item.roi,
                    metadata=item.get_metadata(),
                    subset=item.subset,
                    ignored_label_ids=item.ignored_label_ids,
                )
                items_copy.append(item_copy)

        return Dataset(
            items=items_copy,
            purpose=self.purpose,
            label_schema_id=self.label_schema_id,
            id=generate_uid(),
        )

    def remove(self, item: DatasetItem) -> None:
        """
        Remove an item from the items.
        This function calls remove_at_indices function.

        :raises ValueError: if the input item is not in the dataset
        :param item: the item to be deleted
        """
        index = self.__items.index(item)
        self.remove_at_indices([index])

    def append(self, item: DatasetItem) -> None:
        """
        Append a DatasetItem to the dataset

        :param item: item to append
        """
        if self.dataset_adapter is not None:
            raise ValueError("Cannot append to a dataset with a dataset adapter")
        self.__items.append(item)

    def append_many(self, items: Sequence[DatasetItem]) -> None:
        """
        Append multiple DatasetItems to the dataset

        :param items: items to append
        """
        if self.dataset_adapter is not None:
            raise ValueError("Cannot append to a dataset with a dataset adapter")
        self.__items.extend(items)

    def sort_items(self) -> None:
        """
        Order the dataset, so the items are grouped by media id and roi id.

        :return: None
        """

        def get_sorting_criterion(item: DatasetItem):
            identifier = item.media_identifier
            if isinstance(identifier, VideoFrameIdentifier):
                return identifier.media_id, identifier.frame_index, item.roi_id
            return identifier.media_id, item.roi_id

        self.__items = sorted(self.__items, key=get_sorting_criterion)

    def filter_by_media(self, search_media_identifiers: list[MediaIdentifierEntity]) -> list[DatasetItem]:
        """
        Get item list whose media id is in list of what we want to get

        :param search_media_identifiers: the list of ImageIdentifiers that we want to get
        :return: the items list which the media id is same as ImageIdentifier in search_media_identifiers
        """
        item_list = []
        search_media = {media_identifier.media_id for media_identifier in search_media_identifiers}

        for item in self.__items:
            if item.media_identifier.media_id in search_media:
                item_list.append(item)
        return item_list

    def remove_at_indices(self, indices: list[int]) -> None:
        """
        Delete items based on the `indices`.

        :param indices: the indices of the items that will be deleted from the items.
        """
        indices.sort(reverse=True)  # sort in descending order
        if self.dataset_adapter is not None:
            for i_item in indices:
                self.dataset_adapter.delete_at_index(i_item)
        else:
            for i_item in indices:
                del self._items[i_item]

    def contains_media_id(self, media_id: ID) -> bool:
        """
        Returns True if there are any dataset items which are associated with media_id.

        :param media_id: the id of the media that is being checked.

        :return: True if there are any dataset items which are associated with media_id.
        """
        return any(item.media_identifier.media_id == media_id for item in self.__items)

    def get_label_ids(self, include_empty: bool = False) -> set[ID]:
        """Returns a set of all unique label ID's that are in the dataset.

        Note: This does not respect the ROI of the dataset items.

        :param include_empty: set to True to include empty label (if exists) in the output. Defaults to False.
        :return: list of labels that appear in the dataset
        """
        return set(itertools.chain.from_iterable(item.annotation_scene.get_label_ids(include_empty) for item in self))


class NullDataset(Dataset):
    """Representation of a dataset 'dataset not found'"""

    def __init__(self) -> None:
        super().__init__(creation_date=datetime.datetime.min, id=ID(), ephemeral=False)

    def __repr__(self) -> str:
        return "NullDataset()"

    def append(self, item: DatasetItem) -> None:  # noqa: ARG002
        raise ValueError("Cannot append to a NullDataset")


@dataclass(frozen=True, eq=True)
class DatasetIdentifier:
    """IDs necessary to uniquely identify a Dataset"""

    workspace_id: ID
    project_id: ID
    dataset_storage_id: ID
    dataset_id: ID

    @classmethod
    def from_ds_identifier(
        cls, dataset_storage_identifier: DatasetStorageIdentifier, dataset_id: ID
    ) -> "DatasetIdentifier":
        """
        Factory method to create a DatasetIdentifier from a DatasetStorageIdentifier
        and the ID of the dataset
        """
        return cls(
            workspace_id=dataset_storage_identifier.workspace_id,
            project_id=dataset_storage_identifier.project_id,
            dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
            dataset_id=dataset_id,
        )

    @property
    def ds_identifier(self) -> DatasetStorageIdentifier:
        return DatasetStorageIdentifier(
            workspace_id=self.workspace_id,
            project_id=self.project_id,
            dataset_storage_id=self.dataset_storage_id,
        )
