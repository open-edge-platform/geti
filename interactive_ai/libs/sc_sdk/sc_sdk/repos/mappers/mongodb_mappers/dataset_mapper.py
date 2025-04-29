#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for dataset related entities"""

from threading import Lock
from typing import TYPE_CHECKING
from weakref import WeakValueDictionary

from sc_sdk.adapters.adapter import ProxyAdapter
from sc_sdk.adapters.dataset_adapter import DatasetAdapter
from sc_sdk.entities.annotation import AnnotationScene
from sc_sdk.entities.datasets import Dataset, DatasetIdentifier, DatasetItem, DatasetPurpose
from sc_sdk.entities.subset import Subset
from sc_sdk.entities.video import VideoFrame
from sc_sdk.repos.mappers.mongodb_mapper_interface import (
    IMapperDatasetStorageIdentifierBackward,
    IMapperForward,
    MappingError,
)

from .annotation_mapper import AnnotationToMongo, AnnotationToMongoForwardParameters
from .id_mapper import IDToMongo
from .media_mapper import MediaIdentifierToMongo
from .primitive_mapper import DatetimeToMongo
from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier, Singleton

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class AnnotationSceneCache(metaclass=Singleton):
    """
    Cache used by dataset mappers to ensure that different dataset items referring to
    the same media actually point to the same AnnotationScene Python object after
    deserializing the dataset.
    """

    def __init__(self) -> None:
        # the cache is WeakValueDictionary, so entries are automatically removed when
        # there is no more strong-ref to the respective values (AnnotationScene);
        # in practice, they are cleaned up when the Dataset is no longer used.
        self._shared_lock = Lock()
        self._shared_annotations: MutableMapping[ID, AnnotationScene] = WeakValueDictionary()

    def get_or_load(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        annotation_scene_id: ID,
    ) -> AnnotationScene:
        """
        Get an annotation scene by ID from the cache, if present, or load it from the DB

        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the annotation scene
        :param annotation_scene_id: ID of the annotation scene
        :return: AnnotationScene
        """
        from sc_sdk.repos import AnnotationSceneRepo

        with self._shared_lock:
            annotation_scene = self._shared_annotations.get(annotation_scene_id, None)
            if annotation_scene is None:
                annotation_scene = AnnotationSceneRepo(dataset_storage_identifier).get_by_id(annotation_scene_id)
                self._shared_annotations[annotation_scene_id] = annotation_scene

        return annotation_scene


class DatasetItemToMongo(
    IMapperForward[DatasetItem, dict],
    IMapperDatasetStorageIdentifierBackward[DatasetItem, dict],
):
    """MongoDB mapper for `DatasetItem` entities"""

    @staticmethod
    def forward(instance: DatasetItem) -> dict:
        # Note: by passing media height/width equal to 0, the ROI shape area parameters
        # will be left uninitialized
        annotation_mapper_parameters = AnnotationToMongoForwardParameters(
            media_height=0,
            media_width=0,
        )
        return {
            "_id": IDToMongo.forward(instance.id_),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
            "annotation_scene_id": IDToMongo.forward(instance.annotation_scene.id_),
            "roi": AnnotationToMongo.forward(
                instance.roi,
                parameters=annotation_mapper_parameters,
            ),
            "subset": str(instance.subset),
            "metadata": [IDToMongo.forward(id_) for id_ in instance.metadata_ids],
            "ignored_labels": [IDToMongo.forward(label_id) for label_id in instance.ignored_label_ids],
        }

    @staticmethod
    def backward(instance: dict, dataset_storage_identifier: DatasetStorageIdentifier) -> DatasetItem:
        from sc_sdk.repos import MetadataRepo

        media_type = instance["media_identifier"].get("type", None)
        media_identifier = instance["media_identifier"]

        # Check whether dataset is fully fetched or not
        if media_type == "image":
            from sc_sdk.repos import ImageRepo

            media = ImageRepo(dataset_storage_identifier).get_by_id(
                IDToMongo.backward(instance["media_identifier"]["media_id"])
            )
        elif media_type == "video_frame":
            from sc_sdk.repos import VideoRepo

            video = VideoRepo(dataset_storage_identifier).get_by_id(IDToMongo.backward(media_identifier["media_id"]))
            media = VideoFrame(  # type: ignore
                video=video,
                frame_index=media_identifier["frame_index"],
            )
        else:
            raise MappingError(f"Unknown media type: {media_type}")

        subset = Subset[instance.get("subset", "NONE").upper()]

        annotation_scene_id = IDToMongo.backward(instance["annotation_scene_id"])
        annotation_scene = AnnotationSceneCache().get_or_load(
            dataset_storage_identifier=dataset_storage_identifier,
            annotation_scene_id=annotation_scene_id,
        )

        metadata_ids = [IDToMongo.backward(metadata_id) for metadata_id in instance.get("metadata", [])]
        metadata_repo = MetadataRepo(dataset_storage_identifier)
        metadata_adapters = [
            ProxyAdapter(
                id=metadata_id,
                # capture variable 'metadata_id' because lambda evaluates lazily
                proxy=lambda md_id_=metadata_id: metadata_repo.get_by_id(md_id_),  # type: ignore
            )
            for metadata_id in metadata_ids
        ]

        project_identifier = ProjectIdentifier(
            workspace_id=dataset_storage_identifier.workspace_id,
            project_id=dataset_storage_identifier.project_id,
        )
        ignored_label_ids = {IDToMongo.backward(label_id) for label_id in instance.get("ignored_labels", [])}

        return DatasetItem.with_adapters(
            id_=IDToMongo.backward(instance["_id"]),
            metadata_adapters=metadata_adapters,  # type: ignore
            media=media,
            annotation_scene=annotation_scene,
            roi=AnnotationToMongo.backward(instance["roi"], project_identifier=project_identifier),
            subset=subset,
            ignored_label_ids=ignored_label_ids,
        )


class DatasetToMongo(
    IMapperForward[Dataset, dict],
    IMapperDatasetStorageIdentifierBackward[Dataset, dict],
):
    """MongoDB mapper for `Dataset` entities"""

    @staticmethod
    def forward(instance: Dataset) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "purpose": str(instance.purpose),
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
            "mutable": instance.mutable,
            "label_schema_id": IDToMongo.forward(instance.label_schema_id),
        }

    @staticmethod
    def backward(instance: dict, dataset_storage_identifier: DatasetStorageIdentifier) -> Dataset:
        from sc_sdk.repos.dataset_repo import _DatasetItemRepo

        try:
            purpose = DatasetPurpose[instance["purpose"].upper()]
        except KeyError:
            purpose = DatasetPurpose.INFERENCE

        id_ = IDToMongo.backward(instance["_id"])
        creation_date = DatetimeToMongo.backward(instance.get("creation_date"))
        mutable = instance.get("mutable", True)
        label_schema_id = IDToMongo.backward(instance.get("label_schema_id"))

        dataset_item_repo = _DatasetItemRepo(
            dataset_identifier=DatasetIdentifier.from_ds_identifier(
                dataset_storage_identifier=dataset_storage_identifier,
                dataset_id=id_,
            ),
        )
        dataset_items_docs = dataset_item_repo.get_all_docs()
        dataset_adapter = DatasetAdapter(
            dataset_item_backward_mapper=dataset_item_repo.backward_map,
            dataset_items_docs=dataset_items_docs,
        )

        return Dataset(
            dataset_adapter=dataset_adapter,
            purpose=purpose,
            creation_date=creation_date,
            id=id_,
            mutable=mutable,
            label_schema_id=label_schema_id,
            ephemeral=False,
        )
