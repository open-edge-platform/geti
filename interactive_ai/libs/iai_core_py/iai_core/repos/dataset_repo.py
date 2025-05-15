# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the MongoDB repos for dataset entities"""

import logging
import warnings
from collections import defaultdict
from collections.abc import Callable, Sequence
from functools import partial

import pymongo
from pymongo import IndexModel
from pymongo.client_session import ClientSession
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core.adapters.adapter import ReferenceAdapter
from iai_core.entities.dataset_item import DatasetItem, NullDatasetItem
from iai_core.entities.datasets import Dataset, DatasetIdentifier, DatasetPurpose, NullDataset
from iai_core.entities.metadata import MetadataItem
from iai_core.entities.subset import Subset
from iai_core.repos.annotation_scene_repo import AnnotationSceneRepo
from iai_core.repos.base.dataset_based_repo import DatasetBasedSessionRepo
from iai_core.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from iai_core.repos.base.session_repo import QueryAccessMode
from iai_core.repos.mappers.cursor_iterator import CursorIterator
from iai_core.repos.mappers.mongodb_mappers.dataset_mapper import DatasetItemToMongo, DatasetToMongo
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo
from iai_core.repos.metadata_repo import MetadataRepo
from iai_core.repos.training_revision_filter_repo import _TrainingRevisionFilterRepo
from iai_core.utils.type_helpers import SequenceOrSet

from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, Session

logger = logging.getLogger(__name__)


class _DatasetItemRepo(DatasetBasedSessionRepo[DatasetItem]):
    """
    Repository to persist DatasetItem entities in the database.

    NOTE: this class is semi-private: all database interactions with datasets and their
    items should happen through the DatasetRepo class instead, unless there is a strong
    motivation to bypass DatasetRepo and use this class.

    :param dataset_identifier: Identifier of the dataset
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        dataset_identifier: DatasetIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="dataset_item",
            session=session,
            dataset_identifier=dataset_identifier,
        )
        # external repos are loaded lazily when needed
        self.__annotation_scene_repo: AnnotationSceneRepo | None = None
        self.__metadata_repo: MetadataRepo | None = None

    @property
    def forward_map(self) -> Callable[[DatasetItem], dict]:
        return DatasetItemToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], DatasetItem]:
        return partial(DatasetItemToMongo.backward, dataset_storage_identifier=self.identifier.ds_identifier)

    @property
    def null_object(self) -> NullDatasetItem:
        return NullDatasetItem()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=DatasetItemToMongo,
            parameter=self.identifier.ds_identifier,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("media_identifier", pymongo.DESCENDING)]),
            IndexModel([("annotation_scene_id", pymongo.DESCENDING)]),
        ]
        return super_indexes + new_indexes

    @property
    def annotation_scene_repo(self) -> AnnotationSceneRepo:
        """Annotation scene repo relative to this DatasetItemRepo"""
        if self.__annotation_scene_repo is None:
            self.__annotation_scene_repo = AnnotationSceneRepo(
                dataset_storage_identifier=self.identifier.ds_identifier,
                session=self._session,
            )
        return self.__annotation_scene_repo

    @property
    def metadata_repo(self) -> MetadataRepo:
        """Metadata repo relative to this DatasetItemRepo"""
        if self.__metadata_repo is None:
            self.__metadata_repo = MetadataRepo(
                dataset_storage_identifier=self.identifier.ds_identifier,
                session=self._session,
            )
        return self.__metadata_repo

    def _save_annotations_and_metadata_for_item(
        self,
        dataset_item: DatasetItem,
        already_saved_scenes_ids: set[ID] | None = None,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Store the members of the DatasetItem in their respective repositories

        :param dataset_item: DatasetItem to commit its members for
        :param already_saved_scenes_ids: Set used as cache for the IDs of annotation
            scenes that have been already saved, so will be skipped by this function.
            The set is updated in-place so it can be reused for subsequent calls.
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        # Metadata items are immutable so save them only if not stored to DB yet
        for metadata_item_adapter in dataset_item.metadata_adapters:
            if isinstance(metadata_item_adapter, ReferenceAdapter):
                metadata_item: MetadataItem = metadata_item_adapter.get()
                if metadata_item.ephemeral:
                    self.metadata_repo.save(metadata_item, mongodb_session=mongodb_session)

        # It is not necessary to save the annotation if it was already saved (e.g. referenced by another dataset item)
        annotation_scene_id = dataset_item.annotation_scene.id_
        if already_saved_scenes_ids is None or annotation_scene_id not in already_saved_scenes_ids:
            self.annotation_scene_repo.save(dataset_item.annotation_scene, mongodb_session=mongodb_session)
            if already_saved_scenes_ids is not None:
                already_saved_scenes_ids.add(annotation_scene_id)

    def save_shallow(self, instance: DatasetItem, mongodb_session: ClientSession | None = None) -> None:
        """
        Save a DatasetItem

        This method does NOT save internally referenced entities such as annotations
        and metadata. If you need to save them, use _DatasetItemRepo.save_deep() instead.

        :param instance: DatasetItem to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        super().save(instance, mongodb_session=mongodb_session)

    def save_deep(self, instance: DatasetItem, mongodb_session: ClientSession | None = None) -> None:
        """
        Save a DatasetItem and all the other entities referenced internally,
        including annotations and metadata.

        If you do not need to save annotations and metadata, please consider using
        the more efficient _DatasetItemRepo.save_shallow() method.

        :param instance: DatasetItem to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        self._save_annotations_and_metadata_for_item(instance, mongodb_session=mongodb_session)

        super().save(instance, mongodb_session=mongodb_session)

    def save(self, instance: DatasetItem, mongodb_session: ClientSession | None = None) -> None:
        warnings.warn(
            "_DatasetItemRepo.save() is deprecated; please use more explicit alternatives "
            "like save_deep() or save_shallow().",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.save_deep(instance, mongodb_session=mongodb_session)

    def save_many_shallow(
        self,
        instances: Sequence[DatasetItem],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Save multiple DatasetItems at once.

        This method does NOT save internally referenced entities such as annotations
        and metadata. If you need to save them, use _DatasetItemRepo.save_many_deep().

        :param instances: DatasetItem objects to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        super().save_many(instances, mongodb_session=mongodb_session)

    def save_many_deep(
        self,
        instances: Sequence[DatasetItem],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Save multiple DatasetItems and all the other entities referenced internally
        in the items, including annotations and metadata.

        If you do not need to save annotations and metadata, please consider using
        the more efficient _DatasetItemRepo.save_many_shallow() method.

        :param instances: DatasetItem objects to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        already_saved_scenes_ids: set[ID] = set()
        for instance in instances:
            self._save_annotations_and_metadata_for_item(
                instance,
                already_saved_scenes_ids=already_saved_scenes_ids,
                mongodb_session=mongodb_session,
            )

        super().save_many(instances, mongodb_session=mongodb_session)

    def save_many(
        self,
        instances: Sequence[DatasetItem],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        warnings.warn(
            "_DatasetItemRepo.save_many() is deprecated; please use more explicit "
            "alternatives like save_many_deep() or save_many_shallow().",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.save_many_deep(instances, mongodb_session=mongodb_session)

    def get_all_docs(self) -> list[dict]:
        """
        Get all the DB documents of the dataset items in the dataset

        :return: List of documents
        """
        query = self.preliminary_query_match_filter(QueryAccessMode.READ)
        sort_options = [("_id", 1)]  # sort by id, oldest first
        docs = self._collection.find(query, sort=sort_options)
        return list(docs)

    def sample(self, size: int, subset: Subset | None = None) -> tuple[DatasetItem, ...]:
        """
        Get randomly picked samples of items belonging to the dataset.

        :param size: The number of samples to pick
        :param subset: Optional, the subset of items to filter
        :return: Tuple containing random samples from the dataset
        """
        pipeline: list[dict] = []
        if subset is not None:
            pipeline.append({"$match": {"subset": subset.name}})
        pipeline.append({"$sample": {"size": max(size, 0)}})
        docs = self.aggregate_read(pipeline)
        return tuple(self.backward_map(doc) for doc in docs)

    def get_by_ids(self, dataset_item_ids: Sequence[ID]) -> CursorIterator[DatasetItem]:
        """
        Get one or more dataset items given their IDs and the dataset they belong to

        :param dataset_item_ids: IDs of the dataset items to get
        :return: Cursor over the found dataset items
        :raises ValueError: if the input sequence of items is empty
        """
        if not dataset_item_ids:
            raise ValueError("Empty sequence of dataset item ids")
        match_filter = {
            "_id": {"$in": [IDToMongo.forward(dataset_item_id) for dataset_item_id in dataset_item_ids]},
        }
        return self.get_all(extra_filter=match_filter)

    def get_by_media_identifiers(
        self, media_identifiers: Sequence[MediaIdentifierEntity]
    ) -> CursorIterator[DatasetItem]:
        """
        Get all items in the dataset for a given list of media identifiers

        :param media_identifiers: identifiers of media to fetch the dataset items for
        :raises ValueError: if the input sequence of media identifiers is empty
        """
        if not media_identifiers:
            raise ValueError("Empty sequence of media identifiers")
        match_filter = {
            "media_identifier": {
                "$in": [MediaIdentifierToMongo.forward(identifier) for identifier in media_identifiers]
            },
        }
        return self.get_all(extra_filter=match_filter)

    def get_latest_annotation_scene_id(self, media_identifier: MediaIdentifierEntity | None = None) -> ID:
        """
        Get the ID of the latest (highest ID) annotation scene referenced in the dataset
        and (optionally) relative to a specific media identifier.

        :param media_identifier: Optional, ID of the media identifier
        :return: ID of latest annotation scene, or ID() in case of no match
        """
        match_filter: dict = {}
        if media_identifier is not None:
            match_filter["media_identifier"] = MediaIdentifierToMongo.forward(media_identifier)
        aggr_pipeline: list[dict] = [
            {"$match": match_filter},
            {"$sort": {"annotation_scene_id": -1}},
            {"$limit": 1},
            {"$project": {"annotation_scene_id": 1}},
        ]
        aggr_result = self.aggregate_read(aggr_pipeline)
        try:
            ann_scene_id_doc = next(aggr_result)
        except StopIteration:
            return ID()
        return IDToMongo.backward(ann_scene_id_doc["annotation_scene_id"])

    def count_per_media_type(self) -> dict[str, int]:
        """
        Count the number of images, videos and frames in the dataset.

        :return: Dictionary with the following items:
          - n_images: Number of images
          - n_videos: Number of videos
          - n_frames: Number of video frames
          - n_samples: Number of dataset items
        """
        pipeline = [
            {
                "$facet": {
                    "n_images": [
                        {"$match": {"media_identifier.type": "image"}},
                        {"$group": {"_id": {"media_identifier": "$media_identifier"}}},
                        {"$count": "count"},
                    ],
                    "n_frames": [
                        {"$match": {"media_identifier.type": "video_frame"}},
                        {"$group": {"_id": {"media_identifier": "$media_identifier"}}},
                        {"$count": "count"},
                    ],
                    "n_samples": [
                        {"$count": "count"},
                    ],
                    "n_videos": [
                        {"$match": {"media_identifier.type": "video_frame"}},
                        {"$group": {"_id": "media_identifier.media_id"}},
                        {"$count": "count"},
                    ],
                }
            },
        ]
        docs = self.aggregate_read(pipeline)
        doc = next(docs)
        n_images = doc["n_images"][0].get("count", 0) if len(doc["n_images"]) > 0 else 0
        n_frames = doc["n_frames"][0].get("count", 0) if len(doc["n_frames"]) > 0 else 0
        n_samples = doc["n_samples"][0].get("count", 0) if len(doc["n_samples"]) > 0 else 0
        n_videos = doc["n_videos"][0].get("count", 0) if len(doc["n_videos"]) > 0 else 0
        return {
            "n_images": n_images,
            "n_frames": n_frames,
            "n_videos": n_videos,
            "n_samples": n_samples,
        }

    def count_per_subset(self) -> dict[str, int]:
        """
        Count the number of dataset items in each subset of the dataset

        :return: Dict containing per-subset counts with format {subset: count}.
            The returned subset name is upper-case.
        """
        query = [
            {"$group": {"_id": "$subset", "count": {"$sum": 1}}},
        ]
        docs = self.aggregate_read(query)
        return {doc["_id"].upper(): doc["count"] for doc in docs}

    def __delete_and_get_deleted_items_ids(self, deletion_match_filter: dict) -> tuple[ID, ...]:
        # Find the ids to delete
        ids_to_delete_aggr_pipeline = [
            {"$match": deletion_match_filter},
            {"$project": {"_id": 1}},
        ]
        ids_to_delete_aggr_result = self.aggregate_read(ids_to_delete_aggr_pipeline)
        deleted_ids = tuple(IDToMongo.backward(id_doc["_id"]) for id_doc in ids_to_delete_aggr_result)

        # Delete the documents
        self.delete_all(extra_filter=deletion_match_filter)

        return deleted_ids

    def delete_all_by_media_identifiers(self, media_identifiers: Sequence[MediaIdentifierEntity]) -> tuple[ID, ...]:
        """
        Delete all the dataset items relative to the specified media in a given dataset

        :param media_identifiers: identifiers of the media of the items to remove
        :return: Tuple containing the IDs of the deleted dataset items
        :raises ValueError: if the input sequence of media identifiers is empty
        """
        if not media_identifiers:
            raise ValueError("Empty sequence of media identifiers")
        deletion_match_filter = {
            "media_identifier": {
                "$in": [MediaIdentifierToMongo.forward(identifier) for identifier in media_identifiers]
            },
        }
        return self.__delete_and_get_deleted_items_ids(deletion_match_filter)

    def delete_all_by_media_id(self, media_id: ID) -> tuple[ID, ...]:
        """
        Delete all DatasetItem entities for a given media (video/image) from a dataset

        :param media_id: identifiers of media to remove items for
        :return: A tuple containing the deleted dataset items
        """
        deletion_match_filter = {
            "media_identifier.media_id": IDToMongo.forward(media_id),
        }
        return self.__delete_and_get_deleted_items_ids(deletion_match_filter)

    def assign_items_to_subset(self, dataset_items_ids: Sequence[ID], subset: Subset) -> None:
        """
        Update the subset of one or more dataset items in the database

        :param dataset_items_ids: IDs of the dataset items to update
        :param subset: Subset to assign to the items
        :raises ValueError: if the input sequence of dataset items is empty
        """
        if not dataset_items_ids:
            raise ValueError("Empty sequence of dataset items to assign to subset")
        match_filter: dict = {
            "_id": {"$in": [IDToMongo.forward(id_) for id_ in dataset_items_ids]},
            **self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE),
        }
        update_query = {"$set": {"subset": str(subset)}}
        self._collection.update_many(filter=match_filter, update=update_query)

    def save_ignored_label_ids_for_dataset_item(self, dataset_item_id: ID, label_ids: SequenceOrSet[ID]) -> None:
        """
        Set the ignored labels for a given dataset item

        :param dataset_item_id: ID of the dataset item for which ignored labels are set
        :param label_ids: IDs of the labels
        :raises ValueError: if the input sequence of labels is empty
        """
        if not label_ids:
            raise ValueError("Empty sequence of labels to ignore")
        match_filter: dict = {
            "_id": IDToMongo.forward(dataset_item_id),
            **self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE),
        }
        update_query = {"$set": {"ignored_labels": [IDToMongo.forward(label_id) for label_id in label_ids]}}
        self._collection.update_one(filter=match_filter, update=update_query)


class DatasetRepo(DatasetStorageBasedSessionRepo[Dataset]):
    """
    Repository to persist Dataset entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="dataset",
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def forward_map(self) -> Callable[[Dataset], dict]:
        return DatasetToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], Dataset]:
        return partial(DatasetToMongo.backward, dataset_storage_identifier=self.identifier)

    @property
    def null_object(self) -> NullDataset:
        return NullDataset()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=DatasetToMongo,
            parameter=self.identifier,
        )

    def get_dataset_item_repo(self, dataset_id: ID) -> _DatasetItemRepo:
        return _DatasetItemRepo(
            dataset_identifier=DatasetIdentifier.from_ds_identifier(
                dataset_storage_identifier=self.identifier, dataset_id=dataset_id
            ),
        )

    def get_training_revision_filter_repo(self, dataset_id: ID) -> _TrainingRevisionFilterRepo:
        return _TrainingRevisionFilterRepo(
            dataset_identifier=DatasetIdentifier.from_ds_identifier(
                dataset_storage_identifier=self.identifier, dataset_id=dataset_id
            ),
        )

    def __save(
        self,
        instance: Dataset,
        deepsave: bool,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        if not instance.ephemeral and not instance.mutable:
            raise ValueError(f"Cannot save non-mutable dataset with id `{instance.id_}` twice")

        dataset_item_repo = self.get_dataset_item_repo(instance.id_)
        dataset_items = tuple(instance)
        if dataset_items:
            if deepsave:
                dataset_item_repo.save_many_deep(instances=dataset_items, mongodb_session=mongodb_session)
            else:
                dataset_item_repo.save_many_shallow(instances=dataset_items, mongodb_session=mongodb_session)

            # Save training purpose dataset items to the dataset filter collection
            if instance.purpose == DatasetPurpose.TRAINING:
                training_revision_repo = self.get_training_revision_filter_repo(instance.id_)
                training_revision_repo.save_many(dataset_items)

        else:
            logger.warning(
                "Saving empty dataset with ID `%s` (purpose `%s`) to the DB",
                instance.id_,
                instance.purpose,
            )

        super().save(instance, mongodb_session=mongodb_session)

    def save_shallow(self, instance: Dataset, mongodb_session: ClientSession | None = None) -> None:
        """
        Save a dataset and its items.

        This method does not save the annotation and metadata referenced inside
        the dataset items: if you need this feature, use DatasetRepo.deepsave() instead.

        :param instance: Dataset to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        self.__save(instance, deepsave=False, mongodb_session=mongodb_session)

    def save_deep(self, instance: Dataset, mongodb_session: ClientSession | None = None) -> None:
        """
        Save a dataset, its items and all the other entities referenced internally,
        including annotations and metadata.

        If you do not need to save annotations and metadata, please consider using
        the more efficient DatasetRepo.save() method.

        :param instance: Dataset to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        self.__save(instance, deepsave=True, mongodb_session=mongodb_session)

    def save(self, instance: Dataset, mongodb_session: ClientSession | None = None) -> None:
        warnings.warn(
            "DatasetRepo.save() is deprecated; please use more explicit alternatives "
            "like save_deep() or save_shallow().",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.save_deep(instance, mongodb_session=mongodb_session)

    def save_many(
        self,
        instances: Sequence[Dataset],
        mongodb_session: ClientSession | None = None,
    ) -> None:
        raise NotImplementedError("Saving multiple datasets at once is not supported yet.")

    def add_items_to_dataset(self, dataset_id: ID, dataset_items: Sequence[DatasetItem]) -> None:
        """
        Adds a list of dataset items to a dataset

        :param dataset_id: ID of the Dataset to add the items to
        :param dataset_items: List of DatasetItems to add to the dataset
        :raises ValueError: if the input sequence of items is empty
        """
        if not dataset_items:
            raise ValueError("No items to add")
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        dataset_item_repo.save_many_shallow(instances=dataset_items)

    def get_items_from_dataset(self, dataset_id: ID, dataset_item_ids: Sequence[ID]) -> CursorIterator[DatasetItem]:
        """
        Fetch specific items from a dataset given their IDs

        :param dataset_id: ID of the Dataset containing the items
        :param dataset_item_ids: IDs of the dataset items to fetch
        :return: Tuple containing the retrieved dataset items
        :raises ValueError: if the input sequence of items is empty
        """
        if not dataset_item_ids:
            raise ValueError("Empty sequence of dataset item ids")
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        return dataset_item_repo.get_by_ids(dataset_item_ids=dataset_item_ids)

    def get_items_by_dataset_and_media_identifiers(
        self, dataset_id: ID, media_identifiers: Sequence[MediaIdentifierEntity]
    ) -> CursorIterator[DatasetItem]:
        """
        Get all the items in a dataset that are relative to any of the given media.

        :param dataset_id: ID of the dataset
        :param media_identifiers: identifiers of the media
        :raises ValueError: if the input sequence of media identifiers is empty
        """
        if not media_identifiers:
            raise ValueError("Empty sequence of media identifiers")
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        return dataset_item_repo.get_by_media_identifiers(media_identifiers=media_identifiers)

    def sample(self, dataset_id: ID, size: int, subset: Subset | None = None) -> tuple[DatasetItem, ...]:
        """
        Retrieve randomly picked samples of items belonging to the dataset.

        :param dataset_id: ID of the dataset
        :param size: The number of samples to pick
        :param subset: Optional, the subset of items to filter
        :return: Tuple containing random samples from the dataset
        """
        return self.get_dataset_item_repo(dataset_id).sample(size=size, subset=subset)

    def get_latest_annotation_scene_id(
        self, dataset_id: ID, media_identifier: MediaIdentifierEntity | None = None
    ) -> ID:
        """
        Get the ID of the latest (highest ID) annotation scene that is referenced in
        the specified dataset and (optionally) relative to a given media identifier.

        :param dataset_id: ID of the dataset
        :param media_identifier: Optional, identifier of the media relative to the scene
        :return: ID of latest annotation scene, or ID() in case of no match
        """
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        return dataset_item_repo.get_latest_annotation_scene_id(media_identifier=media_identifier)

    def count_items(self, dataset_id: ID) -> int:
        """
        Get the length of a given dataset, i.e. the total number of dataset items

        :param dataset_id: ID of the dataset
        :return: Total number of items in the dataset
        """
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        return dataset_item_repo.count()

    def count_per_media_type(self, dataset_id: ID) -> dict[str, int]:
        """
        Count the number of images, videos and frames in the dataset.

        :param dataset_id: ID of the dataset
        :return: Dictionary with the following items:
          - n_images: Number of images
          - n_videos: Number of videos
          - n_frames: Number of video frames
          - n_samples: Number of dataset items
        """
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        return dataset_item_repo.count_per_media_type()

    def count_per_subset(self, dataset_id: ID) -> dict[str, int]:
        """
        Count the number of dataset items in each subset of the dataset

        :return: Dict containing per-subset counts with format {subset: count}.
            The returned subset name is upper-case.
        """
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        return dataset_item_repo.count_per_subset()

    def delete_items_by_dataset_and_media_identifiers(
        self, dataset_id: ID, media_identifiers: Sequence[MediaIdentifierEntity]
    ) -> tuple[ID, ...]:
        """
        Delete all DatasetItem entities for a given list of media identifiers from a dataset

        :param dataset_id: ID of the dataset containing the items to remove
        :param media_identifiers: Media identifiers of the items to remove
        :return: Tuple containing the IDs of the dataset items that were deleted
        :raises ValueError: if the input sequence of items is empty
        """
        if not media_identifiers:
            raise ValueError("Empty sequence of media identifiers")
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        return dataset_item_repo.delete_all_by_media_identifiers(media_identifiers=media_identifiers)

    def delete_items_by_dataset_and_media(self, dataset_id: ID, media_id: ID) -> tuple[ID, ...]:
        """
        Delete all DatasetItem entities for a given media (video/image) from a dataset

        :param dataset_id: ID of the dataset containing the items to remove
        :param media_id: Media ID of the items to remove
        :return: Tuple containing the IDs of the dataset items that were deleted
        """
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        return dataset_item_repo.delete_all_by_media_id(media_id=media_id)

    def delete_items_by_dataset(self, dataset_id: ID) -> None:
        """
        Delete all items from a dataset

        :param dataset_id: ID of the dataset containing the items to remove
        """
        dataset_item_repo = self.get_dataset_item_repo(dataset_id)
        dataset_item_repo.delete_all()

    def delete_by_id(self, id_: ID) -> bool:
        """
        Delete a dataset and all its items by ID

        :param id_: ID of the dataset to delete
        """
        # Delete items
        self.delete_items_by_dataset(dataset_id=id_)
        # Delete dataset
        return super().delete_by_id(id_)

    def save_ignored_label_ids_for_dataset_item(
        self, dataset_id: ID, dataset_item_id: ID, label_ids: SequenceOrSet[ID]
    ) -> None:
        """
        Set the ignored labels for a given dataset item

        :param dataset_id: ID of the dataset containing the item
        :param dataset_item_id: ID of the dataset item
        :param label_ids: IDs of the labels
        :raises ValueError: if the input sequence of labels is empty
        """
        if not label_ids:
            raise ValueError("Empty sequence of labels to ignore")
        dataset_item_repo = self.get_dataset_item_repo(dataset_id=dataset_id)
        dataset_item_repo.save_ignored_label_ids_for_dataset_item(dataset_item_id=dataset_item_id, label_ids=label_ids)

    def save_subsets_in_dataset(self, dataset: Dataset) -> None:
        """
        Update the subset of all the items of a dataset in the database.

        The subsets in the repo are replaced with the current subset values of the
        respective dataset item objects.

        :param dataset: Dataset with the new subsets
        """
        # Group the items by subset
        items_by_subset: dict[Subset, list[ID]] = defaultdict(list)
        for item in dataset:
            items_by_subset[item.subset].append(item.id_)

        # Update the subsets
        dataset_item_repo = self.get_dataset_item_repo(dataset.id_)
        for subset, items_in_subset in items_by_subset.items():
            if items_in_subset:
                dataset_item_repo.assign_items_to_subset(dataset_items_ids=items_in_subset, subset=subset)
