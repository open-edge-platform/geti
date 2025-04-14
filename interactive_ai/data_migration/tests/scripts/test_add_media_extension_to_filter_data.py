# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from copy import deepcopy
from uuid import UUID

import pytest
from bson import ObjectId

from migration.scripts.add_media_extension_to_filter_data import AddMediaExtensionToFilterDataMigration
from migration.utils import MongoDBConnection

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("66a0faf070cdf6d0b2ec5f93")


@pytest.fixture
def fxt_filter_data():
    yield [
        {
            "_id": ObjectId("66a360141ad051b7b6ab1901"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": ObjectId("66a360141ad051b7b6ab1921"),
                "type": "image",
            },
        },
        {
            "_id": ObjectId("66a360141ad051b7b6ab1902"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": ObjectId("66a360141ad051b7b6ab1922"),
                "type": "image",
            },
            "media_extension": "JPG",
        },
        {
            "_id": ObjectId("66a360141ad051b7b6ab1903"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": ObjectId("66a360141ad051b7b6ab1931"),
                "type": "video",
            },
        },
        {
            "_id": ObjectId("66a360141ad051b7b6ab1904"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": ObjectId("66a360141ad051b7b6ab1932"),
                "type": "video",
            },
            "media_extension": "MKV",
        },
        {
            "_id": ObjectId("66a360141ad051b7b6ab1905"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": ObjectId("66a360141ad051b7b6ab1932"),
                "type": "video_frame",
            },
        },
        {
            "_id": ObjectId("66a360141ad051b7b6ab1906"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": ObjectId("66a360000000000000000000"),
                "type": "image",
            },
        },
        {
            "_id": ObjectId("66a360141ad051b7b6ab1907"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": ObjectId("66a360000000000000000001"),
                "type": "video_frame",
            },
        },
    ]


@pytest.fixture
def fxt_images():
    yield [
        {
            "_id": ObjectId("66a360141ad051b7b6ab1921"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "extension": "PNG",
        },
        {
            "_id": ObjectId("66a360141ad051b7b6ab1922"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "extension": "should_not_be_looked_up",
        },
    ]


@pytest.fixture
def fxt_videos():
    yield [
        {
            "_id": ObjectId("66a360141ad051b7b6ab1931"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "extension": "MP4",
        },
        {
            "_id": ObjectId("66a360141ad051b7b6ab1932"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "extension": "AVI",
        },
    ]


@pytest.fixture
def fxt_filter_data_with_extension(fxt_filter_data):
    """
    List of documents in the database with the extension field.
    """
    filter_data_with_extension = deepcopy(fxt_filter_data)
    filter_data_with_extension[0]["media_extension"] = "PNG"
    filter_data_with_extension[2]["media_extension"] = "MP4"
    filter_data_with_extension[4]["media_extension"] = "AVI"
    filter_data_with_extension[5]["media_extension"] = "PNG"
    filter_data_with_extension[6]["media_extension"] = "MP4"

    yield filter_data_with_extension


class TestAddMediaExtensionToFilterData:
    def test_upgrade_project(
        self,
        fxt_filter_data,
        fxt_filter_data_with_extension,
        fxt_videos,
        fxt_images,
        request,
    ):
        # Note that MongoMock does not support the update operations
        # specified in the script. Hence, we use the real MongoDB client
        database = MongoDBConnection().client["geti"]
        dataset_storage_filter_data_collection = database.get_collection("dataset_storage_filter_data")
        training_revision_filter_collection = database.get_collection("training_revision_filter")
        image_collection = database.get_collection("image")
        video_collection = database.get_collection("video")

        def cleanup():
            # Remove the documents added during the test
            dataset_storage_filter_data_collection.delete_many(
                {"_id": {"$in": [doc["_id"] for doc in fxt_filter_data]}}
            )
            training_revision_filter_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_filter_data]}})
            image_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_images]}})
            video_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_videos]}})

        request.addfinalizer(cleanup)

        dataset_storage_filter_data_collection.insert_many(fxt_filter_data)
        training_revision_filter_collection.insert_many(fxt_filter_data)
        image_collection.insert_many(fxt_images)
        video_collection.insert_many(fxt_videos)

        AddMediaExtensionToFilterDataMigration.upgrade_project(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
        )

        # Check that the extension field was added to the documents
        dataset_storage_filter_data_after_upgrade = list(
            dataset_storage_filter_data_collection.find(filter={"project_id": PROJECT_ID})
        )
        dataset_storage_filter_data_after_upgrade.sort(key=lambda doc: doc["_id"])
        training_revision_filter_after_upgrade = list(
            training_revision_filter_collection.find(filter={"project_id": PROJECT_ID})
        )
        training_revision_filter_after_upgrade.sort(key=lambda doc: doc["_id"])
        fxt_filter_data_with_extension.sort(key=lambda doc: doc["_id"])
        assert dataset_storage_filter_data_after_upgrade == fxt_filter_data_with_extension
        assert training_revision_filter_after_upgrade == fxt_filter_data_with_extension
