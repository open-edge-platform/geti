# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from copy import deepcopy
from uuid import UUID

import pytest
from bson import ObjectId

from migration.scripts.update_media_score import UpdateMediaScoreMigration
from migration.utils import MongoDBConnection

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("662c1c6b3a3df3291394b158")
MEDIA_SCORE_ID = ObjectId("67a1db26cfb7323389b24864")


@pytest.fixture
def fxt_media_score_document_pre_update() -> dict:
    return {
        "_id": MEDIA_SCORE_ID,
        "organization_id": ORGANIZATION_ID,
        "workspace_id": WORKSPACE_ID,
        "project_id": PROJECT_ID,
        "scores": [
            {"metric": "accuracy", "score": 0.9, "label_id": None},
            {"metric": "f1", "score": 0.8, "label_id": None},
        ],
    }


@pytest.fixture
def fxt_media_score_document_pre_update_mixed(fxt_media_score_document_pre_update) -> dict:
    mixed = deepcopy(fxt_media_score_document_pre_update)
    # modify last score to be already updated, migration script should not change it
    mixed["scores"][-1] = {"name": "f1", "value": 0.8, "type": "score", "label_id": None}
    return mixed


@pytest.fixture
def fxt_media_score_document_post_update() -> dict:
    return {
        "_id": MEDIA_SCORE_ID,
        "organization_id": ORGANIZATION_ID,
        "workspace_id": WORKSPACE_ID,
        "project_id": PROJECT_ID,
        "scores": [
            {"type": "score", "name": "accuracy", "value": 0.9, "label_id": None},
            {"type": "score", "name": "f1", "value": 0.8, "label_id": None},
        ],
    }


class TestUpdateMediaScoreMigration:
    def test_media_score_upgrade(
        self, request, fxt_media_score_document_post_update, fxt_media_score_document_pre_update_mixed
    ) -> None:
        def cleanup():
            # Remove the documents added during the test
            media_score_collection.delete_many({"_id": fxt_media_score_document_pre_update_mixed["_id"]})

        request.addfinalizer(cleanup)

        database = MongoDBConnection().client["geti"]
        media_score_collection = database.get_collection("media_score")
        media_score_collection.insert_one(fxt_media_score_document_pre_update_mixed)

        UpdateMediaScoreMigration.upgrade_project(str(ORGANIZATION_ID), str(WORKSPACE_ID), str(PROJECT_ID))

        updated_media_score_document = media_score_collection.find_one({"_id": MEDIA_SCORE_ID})

        for score in updated_media_score_document["scores"]:
            assert set(score.keys()) == {"name", "value", "type", "label_id"}
        assert updated_media_score_document == fxt_media_score_document_post_update

    def test_media_score_downgrade(
        self, request, fxt_media_score_document_pre_update, fxt_media_score_document_post_update
    ) -> None:
        def cleanup():
            # Remove the documents added during the test
            media_score_collection.delete_many({"_id": fxt_media_score_document_pre_update["_id"]})

        request.addfinalizer(cleanup)

        database = MongoDBConnection().client["geti"]
        media_score_collection = database.get_collection("media_score")
        media_score_collection.insert_one(fxt_media_score_document_post_update)

        UpdateMediaScoreMigration.downgrade_project(str(ORGANIZATION_ID), str(WORKSPACE_ID), str(PROJECT_ID))

        downgraded_media_score_document = media_score_collection.find_one({"_id": MEDIA_SCORE_ID})

        for score in downgraded_media_score_document["scores"]:
            assert set(score.keys()) == {"metric", "score", "label_id"}
        assert downgraded_media_score_document == fxt_media_score_document_pre_update
