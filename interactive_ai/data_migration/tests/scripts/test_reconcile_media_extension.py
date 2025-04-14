# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from copy import deepcopy
from uuid import uuid4

import pytest
from bson import ObjectId

from migration.scripts.reconcile_media_extension import ReconcileMediaExtensionMigration
from migration.utils import MongoDBConnection


@pytest.fixture
def fxt_organization_id():
    yield uuid4()


@pytest.fixture
def fxt_workspace_id():
    yield uuid4()


@pytest.fixture
def fxt_project_ids():
    yield ObjectId(), ObjectId()  # 2 projects


@pytest.fixture
def fxt_images_before_upgrade(fxt_organization_id, fxt_workspace_id, fxt_project_ids):
    """List of documents present in the database BEFORE upgrading project #0"""
    yield [
        # document in project #0 with inconsistent 'extension' and 'binary_filename' -> expected that it is updated
        {
            "_id": ObjectId(),
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_ids[0],
            "extension": "WEBP",
            "binary_filename": "foo.jpg",
        },
        # document in project #0 with consistent 'extension' and 'binary_filename' -> expected that it is NOT updated
        {
            "_id": ObjectId(),
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_ids[0],
            "extension": "WEBP",
            "binary_filename": "bar.webp",
        },
        # document in project #0 without 'binary_filename' -> expected that it is NOT updated
        {
            "_id": ObjectId(),
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_ids[0],
            "extension": "WEBP",
        },
        # document from another project -> expected that it is NOT updated
        {
            "_id": ObjectId(),
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_ids[1],
            "extension": "BMP",
            "binary_filename": "baz.jpg",
        },
    ]


@pytest.fixture
def fxt_images_after_upgrade(fxt_images_before_upgrade):
    """List of documents present in the database AFTER upgrading project #0"""
    docs_after_upgrade = deepcopy(fxt_images_before_upgrade)
    docs_after_upgrade[0].update({"extension": "JPG"})
    yield docs_after_upgrade


class TestReconcileMediaExtensionMigration:
    def test_upgrade_project(
        self,
        request,
        fxt_organization_id,
        fxt_workspace_id,
        fxt_project_ids,
        fxt_images_before_upgrade,
        fxt_images_after_upgrade,
    ) -> None:
        def cleanup():
            # Remove the documents added during the test
            image_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_images_before_upgrade]}})

        request.addfinalizer(cleanup)

        # Note that MongoMock does not support the update operations
        # specified in the script. Hence, we use the real MongoDB client
        database = MongoDBConnection().client["geti"]
        image_collection = database.get_collection("image")
        image_collection.insert_many(fxt_images_before_upgrade)
        project_to_upgrade_id = fxt_project_ids[0]

        ReconcileMediaExtensionMigration.upgrade_project(
            organization_id=str(fxt_organization_id),
            workspace_id=str(fxt_workspace_id),
            project_id=str(project_to_upgrade_id),
        )
        ReconcileMediaExtensionMigration.upgrade_project(
            organization_id=str(fxt_organization_id),
            workspace_id=str(fxt_workspace_id),
            project_id=str(project_to_upgrade_id),
        )

        actual_images_after_upgrade = list(image_collection.find())
        actual_images_after_upgrade.sort(key=lambda doc: doc["_id"])
        fxt_images_after_upgrade.sort(key=lambda doc: doc["_id"])
        assert actual_images_after_upgrade == fxt_images_after_upgrade
