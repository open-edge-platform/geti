# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

import pytest
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.subset import Subset
from sc_sdk.repos import DatasetRepo


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
