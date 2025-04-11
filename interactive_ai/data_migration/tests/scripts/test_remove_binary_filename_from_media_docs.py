# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

from migration.scripts.remove_binary_filename_from_media_docs import RemoveBinaryFilenameFromMediaDocsMigration
from migration.utils import MongoDBConnection

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("66a0faf070cdf6d0b2ec5f93")


def create_dummy_media(media_type: str, num_media: int):
    """
    List of documents in the database with the binary_filename field.
    """
    if media_type not in ["image", "video"]:
        raise ValueError("media_type must be either 'image' or 'video'")

    # Example extensions for images and videos - some in lowercase and some in uppercase
    example_extensions = {
        "image": ["jpg", "JPG", "png", "PNG"],
        "video": ["mp4", "MP4", "mkv", "MKV"],
    }

    media = []
    for i in range(num_media):
        extension = example_extensions[media_type][i % len(example_extensions)]
        media_id = ObjectId(str(i).zfill(24))
        media.append(
            {
                "_id": media_id,
                "organization_id": ORGANIZATION_ID,
                "workspace_id": WORKSPACE_ID,
                "project_id": PROJECT_ID,
                "binary_filename": f"filename{i}.{extension}",
                "extension": extension.upper(),
            }
        )

    return media


@pytest.fixture()
def fxt_videos_with_binary_filename():
    """
    List of documents in the database with the binary_filename field.
    """
    yield create_dummy_media("video", 100)


@pytest.fixture()
def fxt_images_without_binary_filename(fxt_videos_with_binary_filename):
    """
    List of documents in the database without the binary_filename field.
    """
    fxt_videos_without_binary_filename = deepcopy(fxt_videos_with_binary_filename)
    for video in fxt_videos_without_binary_filename:
        # pop
        video.pop("binary_filename")
    yield fxt_videos_without_binary_filename


@pytest.fixture()
def fxt_images_with_binary_filename():
    """
    List of documents in the database with the binary_filename field.
    """
    yield create_dummy_media("image", 100)


@pytest.fixture()
def fxt_videos_without_binary_filename(fxt_images_with_binary_filename):
    """
    List of documents in the database without the binary_filename field.
    """
    fxt_images_without_binary_filename = deepcopy(fxt_images_with_binary_filename)
    for image in fxt_images_without_binary_filename:
        image.pop("binary_filename")
    yield fxt_images_without_binary_filename


class TestRemoveBinaryFilenameFromMediaDocsMigration:
    def test_upgrade_project(
        self,
        fxt_videos_with_binary_filename,
        fxt_videos_without_binary_filename,
        fxt_images_with_binary_filename,
        fxt_images_without_binary_filename,
        request,
    ):
        def cleanup():
            # Remove the documents added during the test
            video_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_videos_with_binary_filename]}})
            image_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_images_with_binary_filename]}})

        request.addfinalizer(cleanup)

        database = MongoDBConnection().client["geti"]
        video_collection = database.get_collection("video")
        image_collection = database.get_collection("image")

        video_collection.insert_many(fxt_videos_with_binary_filename)
        image_collection.insert_many(fxt_images_with_binary_filename)

        RemoveBinaryFilenameFromMediaDocsMigration.upgrade_project(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
        )

        # Check that the binary_filename field was removed from the documents
        for collection_name, fxt_docs in [
            ("video", fxt_videos_with_binary_filename),
            ("image", fxt_images_with_binary_filename),
        ]:
            media_collection = database.get_collection(collection_name)
            for fxt_doc in fxt_docs:
                doc = media_collection.find_one({"_id": fxt_doc["_id"]})
                assert "binary_filename" not in doc

    def test_downgrade_project(
        self,
        fxt_videos_with_binary_filename,
        fxt_videos_without_binary_filename,
        fxt_images_with_binary_filename,
        fxt_images_without_binary_filename,
        request,
    ):
        def cleanup():
            # Remove the documents added during the test
            video_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_videos_without_binary_filename]}})
            image_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_images_without_binary_filename]}})

        request.addfinalizer(cleanup)

        database = MongoDBConnection().client["geti"]
        video_collection = database.get_collection("video")
        image_collection = database.get_collection("image")

        video_collection.insert_many(fxt_videos_without_binary_filename)
        image_collection.insert_many(fxt_images_without_binary_filename)

        RemoveBinaryFilenameFromMediaDocsMigration.downgrade_project(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
        )

        # Check that the binary_filename field was added back to the documents with the format _id.extension
        for collection_name, fxt_docs in [
            ("video", fxt_videos_without_binary_filename),
            ("image", fxt_images_without_binary_filename),
        ]:
            media_collection = database.get_collection(collection_name)
            for fxt_doc in fxt_docs:
                doc = media_collection.find_one({"_id": fxt_doc["_id"]})
                assert "binary_filename" in doc
                assert doc["binary_filename"] == f"{fxt_doc['_id']}.{fxt_doc['extension'].lower()}"
