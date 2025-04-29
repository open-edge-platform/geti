# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from uuid import UUID

import pytest
from bson import ObjectId

from migration.scripts.image_size_as_integer import ImageSizeToIntegerMigration
from migration.utils import MongoDBConnection


@pytest.fixture
def image_size_as_string():
    yield {
        "_id": ObjectId("667ab9880771dbd91fa7139e"),
        "size": "166587",
        "organization_id": UUID("ddb856d6-daf1-4d32-96ad-cac008421c08"),
        "project_id": ObjectId("667ac14a0771dbd91fa714b8"),
        "workspace_id": UUID("de81543b-4428-4693-8685-6a982241789e"),
    }


@pytest.fixture
def image_size_as_integer():
    yield {
        "_id": ObjectId("667ab9880771dbd91fa7139e"),
        "size": 166587,
        "organization_id": UUID("ddb856d6-daf1-4d32-96ad-cac008421c08"),
        "project_id": ObjectId("667ac14a0771dbd91fa714b8"),
        "workspace_id": UUID("de81543b-4428-4693-8685-6a982241789e"),
    }


class TestImageSizeToInteger:
    def test_save_image_size_as_integer(self, image_size_as_string, image_size_as_integer, request):
        """
        Test that the image size is saved as an integer in the object storage
        """
        db = MongoDBConnection().client["geti"]
        collection = db["image"]
        collection.insert_one(image_size_as_string)
        request.addfinalizer(lambda: collection.delete_one({"_id": image_size_as_integer["_id"]}))

        ImageSizeToIntegerMigration.upgrade_project(
            organization_id=str(image_size_as_string["organization_id"]),
            project_id=str(image_size_as_string["project_id"]),
            workspace_id=str(image_size_as_string["workspace_id"]),
        )

        assert collection.find_one() == image_size_as_integer
