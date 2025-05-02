# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID
from iai_core.entities.compiled_dataset_shards import (
    CompiledDatasetShard,
    CompiledDatasetShards,
    NullCompiledDatasetShards,
)
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset
from iai_core.entities.image import Image
from iai_core.entities.subset import Subset
from iai_core.entities.video import VideoFrame
from iai_core.repos import DatasetRepo


@pytest.fixture
def fxt_dataset(fxt_dataset_item, fxt_dataset_storage, fxt_mongo_id):
    """Dataset with 3 items, belonging to train, valid and test subsets, respectively"""

    items = [
        fxt_dataset_item(index=1, subset=Subset.TRAINING),
        fxt_dataset_item(index=2, subset=Subset.VALIDATION),
        fxt_dataset_item(index=3, subset=Subset.TESTING),
    ]
    dataset = Dataset(items=items, id=fxt_mongo_id(1))
    yield dataset


@pytest.fixture
def fxt_dataset_item(fxt_image_entity_factory, fxt_video_frame_entity_factory, fxt_annotation_scene):
    """
    DatasetItem with a media and annotation
    The subset can be specified by parameter.
    """

    def _build_item(
        index: int = 1,
        subset: Subset = Subset.NONE,
        cropped: bool = False,
        media_type: type(Image) = Image,
        video_id_index: int = 1,
    ):
        if cropped:
            roi = fxt_annotation_scene.annotations[0]
        else:
            roi = None

        if media_type == Image:
            media_factory = fxt_image_entity_factory
        elif media_type == VideoFrame:

            def media_factory(index):
                return fxt_video_frame_entity_factory(index=index, video_id_index=video_id_index)

        else:
            raise TypeError

        return DatasetItem(
            media=media_factory(index=index),
            annotation_scene=fxt_annotation_scene,
            roi=roi,
            subset=subset,
            id_=DatasetRepo.generate_id(),
        )

    yield _build_item


@pytest.fixture
def fxt_dataset_items_with_image_data(fxt_dataset_item, monkeypatch):
    """Dataset with 10 items which are able to get the image numpy data"""
    yield [fxt_dataset_item(index=i, subset=Subset.TRAINING, media_type=Image) for i in range(10)]


@pytest.fixture
def fxt_dataset_items_with_video_frame_data(fxt_dataset_item, monkeypatch):
    """Dataset with 10 items which are able to get the video frame numpy data"""
    yield [
        fxt_dataset_item(
            index=i,
            subset=Subset.TRAINING,
            media_type=VideoFrame,
            video_id_index=video_id_index,
        )
        for i in range(5)
        for video_id_index in range(2)
    ]


@pytest.fixture
def fxt_dataset_non_empty(fxt_dataset_item, fxt_dataset_storage, fxt_mongo_id):
    """Dataset with 3 items, belonging to train, valid and test subsets, respectively"""

    items = [
        fxt_dataset_item(index=1, subset=Subset.TRAINING),
        fxt_dataset_item(index=2, subset=Subset.VALIDATION),
        fxt_dataset_item(index=3, subset=Subset.TESTING),
    ]
    dataset = Dataset(items=items, id=fxt_mongo_id(1))
    yield dataset


@pytest.fixture
def fxt_dataset_invalid_subset(fxt_dataset_item, fxt_dataset_storage, fxt_mongo_id):
    """
    Dataset with 4 items, one belonging to train, valid and test subsets, and one item
    belonging to 'NONE' subset
    """

    items = [
        fxt_dataset_item(index=1, subset=Subset.TRAINING),
        fxt_dataset_item(index=2, subset=Subset.VALIDATION),
        fxt_dataset_item(index=3, subset=Subset.TESTING),
        fxt_dataset_item(index=4, subset=Subset.NONE),
    ]
    dataset = Dataset(items=items, id=fxt_mongo_id(2))
    yield dataset


@pytest.fixture
def fxt_empty_dataset(fxt_dataset_storage, fxt_mongo_id):
    """Empty dataset"""
    yield Dataset(items=[], id=fxt_mongo_id(100))


@pytest.fixture()
def fxt_subsets():
    """Three subsets"""
    return Subset.TRAINING, Subset.VALIDATION, Subset.TESTING


@pytest.fixture()
def fxt_dataset_id(fxt_mongo_id):
    return fxt_mongo_id(1003)


@pytest.fixture()
def fxt_dataset_with_images(fxt_dataset_id, fxt_dataset_items_with_image_data, fxt_subsets):
    """Dataset having 10 images and the three subsets."""
    items = []

    for idx, item in enumerate(fxt_dataset_items_with_image_data):
        item.subset = fxt_subsets[idx % len(fxt_subsets)]
        items.append(item)

    return Dataset(id=fxt_dataset_id, items=items)


@pytest.fixture()
def fxt_dataset_with_video_frames(fxt_dataset_id, fxt_dataset_items_with_video_frame_data):
    """Dataset having 5 video frames for two videos respectively"""
    return Dataset(id=fxt_dataset_id, items=fxt_dataset_items_with_video_frame_data)


@pytest.fixture
def fxt_norm_compiled_dataset_shards(fxt_dataset_id: ID, fxt_label_schema_id: ID) -> CompiledDatasetShards:
    return CompiledDatasetShards(
        dataset_id=fxt_dataset_id,
        label_schema_id=fxt_label_schema_id,
        compiled_shard_files=[
            CompiledDatasetShard(
                filename="dummy.arrow",
                binary_filename="dummy.arrow",
                size=10,
                checksum="asdf",
            )
        ],
    )


@pytest.fixture
def fxt_null_compiled_dataset_shards() -> NullCompiledDatasetShards:
    return NullCompiledDatasetShards()


@pytest.fixture(params=["fxt_norm_compiled_dataset_shards", "fxt_null_compiled_dataset_shards"])
def fxt_compiled_dataset_shards(request):
    return request.getfixturevalue(request.param)
