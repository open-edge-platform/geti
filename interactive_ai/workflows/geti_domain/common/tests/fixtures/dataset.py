# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID, DatasetStorageIdentifier
from iai_core_py.entities.compiled_dataset_shards import (
    CompiledDatasetShard,
    CompiledDatasetShards,
    NullCompiledDatasetShards,
)
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.datasets import Dataset
from iai_core_py.entities.image import Image
from iai_core_py.entities.label_schema import LabelSchema
from iai_core_py.entities.subset import Subset
from iai_core_py.entities.video import VideoFrame
from iai_core_py.repos import DatasetRepo

from tests.test_helpers import (
    generate_random_annotated_project,
    generate_training_dataset_of_all_annotated_media_in_project,
)


@pytest.fixture
def fxt_dataset_item(fxt_image_entity_factory, fxt_video_factory, fxt_video_frame_entity_factory, fxt_annotation_scene):
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
                video = fxt_video_factory(index=video_id_index)
                return fxt_video_frame_entity_factory(video=video, index=index)

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
def fxt_dataset_items_with_video_frame_data(fxt_dataset_item, fxt_subsets, monkeypatch):
    """Dataset with 10 items which are able to get the video frame numpy data"""
    yield [
        fxt_dataset_item(
            index=i,
            subset=fxt_subsets[i % 3],
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
def fxt_empty_dataset(fxt_dataset_storage, fxt_mongo_id):
    """Empty dataset"""
    yield Dataset(items=[], id=fxt_mongo_id(100))


@pytest.fixture
def fxt_dataset(fxt_dataset_non_empty):
    yield fxt_dataset_non_empty


@pytest.fixture()
def fxt_dataset_id(fxt_mongo_id):
    return fxt_mongo_id(1003)


@pytest.fixture()
def fxt_subsets():
    """Three subsets"""
    return Subset.TRAINING, Subset.VALIDATION, Subset.TESTING


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


@pytest.fixture
def fxt_dataset_item_anomalous(fxt_image_entity_factory, fxt_annotation_scene_anomalous):
    """
    DatasetItem with a media and anomalous annotation.
    The subset can be specified by parameter.
    """

    def _build_item(index: int = 1, subset: Subset = Subset.NONE):
        return DatasetItem(
            media=fxt_image_entity_factory(index=index),
            annotation_scene=fxt_annotation_scene_anomalous,
            subset=subset,
            id_=DatasetRepo.generate_id(),
        )

    yield _build_item


@pytest.fixture(
    params=[
        "classification",
        "segmentation",
        "detection",
        "anomaly_detection",
        "instance_segmentation",
        "anomaly_segmentation",
        "anomaly_classification",
        "rotated_detection",
        "keypoint_detection",
    ]
)
def fxt_dataset_and_label_schema(
    request: pytest.FixtureRequest,
) -> tuple[DatasetStorageIdentifier, Dataset, LabelSchema]:
    model_template_id = request.param
    project, label_schema = generate_random_annotated_project(
        request,
        name="__Test dataset entities (1)",
        description="TestDataset()",
        model_template_id=model_template_id,
        number_of_images=12,
        number_of_videos=1,
        # This is required by OTX training classification task code
        # We need to compare `Label` equivalance
        # `color (rgba)` and `hotkey` are used to the comparison.
        label_configs=[
            {"name": "rectangle", "color": "#00ff00ee", "hotkey": "ctrl-1"},
            {"name": "ellipse", "color": "#0000ff99", "hotkey": "ctrl-2"},
            {"name": "triangle", "color": "#ff000011", "hotkey": "ctrl-3"},
        ],
    )

    (
        dataset_storage_identifier,
        dataset,
    ) = generate_training_dataset_of_all_annotated_media_in_project(project=project, ignore_some_labels=True)
    return dataset_storage_identifier, dataset, label_schema
