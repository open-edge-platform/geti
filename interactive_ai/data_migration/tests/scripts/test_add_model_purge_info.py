# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from copy import deepcopy
from uuid import UUID

import pytest
from bson import ObjectId

from migration.scripts.add_model_purge_info import AddModelPurgeInfoMigration
from migration.utils import MongoDBConnection

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("66a0faf070cdf6d0b2ec5f93")


@pytest.fixture
def fxt_models_before_upgrade():
    """
    List of documents in the database without the extension field.
    """
    yield [
        {
            "_id": ObjectId("66a360141ad051b7b6ab1939"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
        },
        {
            "_id": ObjectId("66a360371ad051b7b6ab193a"),
            "organization_id": ORGANIZATION_ID,
            "workspace_id": WORKSPACE_ID,
            "project_id": PROJECT_ID,
            "purge_info": {"is_purged": True},
        },
    ]


@pytest.fixture
def fxt_models_after_upgrade(fxt_models_before_upgrade):
    """
    List of documents in the database with the purge info field.
    """
    models_with_purge_info = deepcopy(fxt_models_before_upgrade)
    models_with_purge_info[0]["purge_info"] = {"is_purged": False}
    yield models_with_purge_info


class TestAddPurgeInfoMigration:
    def test_upgrade_project(self, fxt_models_before_upgrade, fxt_models_after_upgrade, request):
        def cleanup():
            # Remove the documents added during the test
            model_collection.delete_many({"_id": {"$in": [doc["_id"] for doc in fxt_models_before_upgrade]}})

        request.addfinalizer(cleanup)
        database = MongoDBConnection().client["geti"]
        model_collection = database.get_collection("model")

        model_collection.insert_many(fxt_models_before_upgrade)

        AddModelPurgeInfoMigration.upgrade_project(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
        )

        models_after_upgrade = list(model_collection.find(filter={"project_id": PROJECT_ID}))
        models_after_upgrade.sort(key=lambda doc: doc["_id"])
        fxt_models_after_upgrade.sort(key=lambda doc: doc["_id"])
        assert models_after_upgrade == fxt_models_after_upgrade
