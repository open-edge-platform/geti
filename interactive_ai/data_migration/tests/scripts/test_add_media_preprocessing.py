# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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


from copy import deepcopy
from uuid import UUID

import pytest
from bson import ObjectId

from migration.scripts.add_media_preprocessing import AddMediaPreprocessingMigration
from migration.utils import MongoDBConnection

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("66a0faf070cdf6d0b2ec5f93")


def create_dummy_documents(collection_name: str, num_docs: int):
    if collection_name not in ["image", "video", "dataset_storage_filter"]:
        raise ValueError("collection_name must be one of: 'image', 'video' or 'dataset_storage_filter'")

    docs = []
    for i in range(num_docs):
        doc_id = ObjectId(str(i).zfill(24))
        docs.append(
            {
                "_id": doc_id,
                "organization_id": ORGANIZATION_ID,
                "workspace_id": WORKSPACE_ID,
                "project_id": PROJECT_ID,
            }
        )

    return docs


@pytest.fixture()
def fxt_videos():
    yield create_dummy_documents("video", 100)


@pytest.fixture()
def fxt_videos_with_preprocessing(fxt_videos):
    videos_with_preprocessing = deepcopy(fxt_videos)
    for video in videos_with_preprocessing:
        video["preprocessing"] = {"status": "FINISHED"}
    yield videos_with_preprocessing


@pytest.fixture()
def fxt_images():
    yield create_dummy_documents("image", 100)


@pytest.fixture()
def fxt_images_with_preprocessing(fxt_images):
    images_with_preprocessing = deepcopy(fxt_images)
    for image in images_with_preprocessing:
        # pop
        image["preprocessing"] = {"status": "FINISHED"}
    yield images_with_preprocessing


@pytest.fixture()
def fxt_dataset_storage_filters():
    yield create_dummy_documents("dataset_storage_filter", 100)


@pytest.fixture()
def fxt_dataset_storage_filters_with_preprocessing(fxt_dataset_storage_filters):
    dataset_storage_filters_with_preprocessing = deepcopy(fxt_dataset_storage_filters)
    for dataset_storage_filter in dataset_storage_filters_with_preprocessing:
        # pop
        dataset_storage_filter["preprocessing"] = "FINISHED"
    yield dataset_storage_filters_with_preprocessing


class TestRemoveBinaryFilenameFromMediaDocsMigration:
    def test_upgrade_project(
        self,
        fxt_videos,
        fxt_images,
        fxt_dataset_storage_filters,
        request,
    ):
        def cleanup():
            # Remove the documents added during the test
            video_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_videos]}})
            image_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_images]}})
            dataset_storage_filter_collection.delete_many(
                {"_id": {"$in": [doc["_id"] for doc in fxt_dataset_storage_filters]}}
            )

        request.addfinalizer(cleanup)

        database = MongoDBConnection().client["geti"]
        video_collection = database.get_collection("video")
        image_collection = database.get_collection("image")
        dataset_storage_filter_collection = database.get_collection("dataset_storage_filter")

        video_collection.insert_many(fxt_videos)
        image_collection.insert_many(fxt_images)
        dataset_storage_filter_collection.insert_many(fxt_dataset_storage_filters)

        AddMediaPreprocessingMigration.upgrade_project(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
        )

        # Check that the binary_filename field was removed from the documents
        for collection_name, fxt_docs, preprocessing in [
            ("video", fxt_videos, {"status": "FINISHED"}),
            ("image", fxt_images, {"status": "FINISHED"}),
            ("dataset_storage_filter", fxt_dataset_storage_filters, "FINISHED"),
        ]:
            collection = database.get_collection(collection_name)
            for fxt_doc in fxt_docs:
                doc = collection.find_one({"_id": fxt_doc["_id"]})
                assert "preprocessing" in doc
                assert doc["preprocessing"] == preprocessing

    def test_downgrade_project(
        self,
        fxt_videos_with_preprocessing,
        fxt_images_with_preprocessing,
        fxt_dataset_storage_filters_with_preprocessing,
        request,
    ):
        def cleanup():
            # Remove the documents added during the test
            video_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_videos_with_preprocessing]}})
            image_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_images_with_preprocessing]}})
            dataset_storage_filter_collection.delete_many(
                {"_id": {"$in": [doc["_id"] for doc in fxt_dataset_storage_filters_with_preprocessing]}}
            )

        request.addfinalizer(cleanup)

        database = MongoDBConnection().client["geti"]
        video_collection = database.get_collection("video")
        image_collection = database.get_collection("image")
        dataset_storage_filter_collection = database.get_collection("dataset_storage_filter")

        video_collection.insert_many(fxt_videos_with_preprocessing)
        image_collection.insert_many(fxt_images_with_preprocessing)
        dataset_storage_filter_collection.insert_many(fxt_dataset_storage_filters_with_preprocessing)

        AddMediaPreprocessingMigration.downgrade_project(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
        )

        # Check that the binary_filename field was added back to the documents with the format _id.extension
        for collection_name, fxt_docs in [
            ("video", fxt_videos_with_preprocessing),
            ("image", fxt_images_with_preprocessing),
            ("dataset_storage_filter", fxt_dataset_storage_filters_with_preprocessing),
        ]:
            collection = database.get_collection(collection_name)
            for fxt_doc in fxt_docs:
                doc = collection.find_one({"_id": fxt_doc["_id"]})
                assert "preprocessing" not in doc
