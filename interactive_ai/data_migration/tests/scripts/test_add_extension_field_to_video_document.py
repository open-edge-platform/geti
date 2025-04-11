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

from migration.scripts.add_extension_field_to_video_document import AddExtensionFieldToVideo
from migration.utils import MongoDBConnection

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("66a0faf070cdf6d0b2ec5f93")


@pytest.fixture
def fxt_videos_without_extension():
    """
    List of documents in the database without the extension field.
    """
    yield [
        {
            "_id": ObjectId("66a360141ad051b7b6ab1939"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "binary_filename": "filename_without_dots.mp4",
        },
        {
            "_id": ObjectId("66a360371ad051b7b6ab193a"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "binary_filename": "filename.with.dots.mkv",
        },
    ]


@pytest.fixture
def fxt_videos_with_extension(fxt_videos_without_extension):
    """
    List of documents in the database with the extension field.
    """
    videos_with_extension = deepcopy(fxt_videos_without_extension)
    # manually add .mp4 and .mkv as it's only for two documents
    videos_with_extension[0]["extension"] = "MP4"
    videos_with_extension[1]["extension"] = "MKV"
    yield videos_with_extension


class TestAddExtensionFieldToVideo:
    def test_upgrade_project(self, fxt_videos_without_extension, fxt_videos_with_extension, request):
        def cleanup():
            # Remove the documents added during the test
            video_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_videos_without_extension]}})

        request.addfinalizer(cleanup)

        # Note that MongoMock does not support the update operations
        # specified in the script. Hence, we use the real MongoDB client
        database = MongoDBConnection().client["geti"]
        video_collection = database.get_collection("video")

        video_collection.insert_many(fxt_videos_without_extension)

        AddExtensionFieldToVideo.upgrade_project(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
        )

        # Check that the extension field was added to the documents
        videos_after_upgrade = list(video_collection.find(filter={"project_id": PROJECT_ID}))
        videos_after_upgrade.sort(key=lambda doc: doc["_id"])
        fxt_videos_with_extension.sort(key=lambda doc: doc["_id"])
        assert videos_after_upgrade == fxt_videos_with_extension
