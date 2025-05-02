# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset
from iai_core.entities.subset import Subset
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
def fxt_dataset_item(fxt_image_entity_factory, fxt_annotation_scene):
    """
    DatasetItem with a media and annotation
    The subset can be specified by parameter.
    """

    def _build_item(index: int = 1, subset: Subset = Subset.NONE, cropped: bool = False):
        if cropped:
            roi = fxt_annotation_scene.annotations[0]
        else:
            roi = None
        return DatasetItem(
            media=fxt_image_entity_factory(index=index),
            annotation_scene=fxt_annotation_scene,
            roi=roi,
            subset=subset,
            id_=DatasetRepo.generate_id(),
        )

    yield _build_item


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
def fxt_dataset_non_empty_2(fxt_dataset_item, fxt_dataset_storage, fxt_mongo_id):
    """Dataset with 3 items, belonging to train, valid and test subsets, respectively"""

    items = [
        fxt_dataset_item(index=4, subset=Subset.TRAINING),
        fxt_dataset_item(index=5, subset=Subset.VALIDATION),
        fxt_dataset_item(index=6, subset=Subset.TESTING),
    ]
    dataset = Dataset(items=items, id=fxt_mongo_id(2))
    yield dataset
