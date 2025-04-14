# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch
from uuid import UUID

import mongomock
import pytest
from bson import ObjectId
from pymongo import MongoClient

from migration.scripts.remove_result_set_and_model_test_result import RemoveResultSetAndModelTestResultMigration
from migration.utils import MongoDBConnection


class TestRemoveResultSetAndModelTestResultMigration:
    @pytest.mark.parametrize("collection_exists", [True, False], ids=["existing", "non-existing"])
    def test_upgrade_non_project_data(self, collection_exists) -> None:
        mock_db = mongomock.MongoClient(uuidRepresentation="standard").db
        if collection_exists:
            mock_db.create_collection("result_set")
            mock_db.create_collection("model_test_result")
            assert "result_set" in mock_db.list_collection_names()
            assert "model_test_result" in mock_db.list_collection_names()

        with (
            patch.object(MongoClient, "get_database", return_value=mock_db),
        ):
            RemoveResultSetAndModelTestResultMigration.upgrade_non_project_data()

        assert mock_db.get_collection("result_set").count_documents({}) == 0
        assert mock_db.get_collection("model_test_result").count_documents({}) == 0

    @pytest.mark.parametrize("collection_exists", [True, False], ids=["existing", "non-existing"])
    def test_upgrade_project(self, collection_exists, request) -> None:
        def cleanup():
            # Remove the documents added during the test
            result_set_collection.delete_many({})
            model_test_result_collection.delete_many({})

        database = MongoDBConnection().client["geti"]
        request.addfinalizer(cleanup)
        result_set_collection = database.get_collection("result_set")
        model_test_result_collection = database.get_collection("model_test_result")
        organization_id = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
        workspace_id = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
        project_id = ObjectId("66a0faf070cdf6d0b2ec5f93")
        filter_query = {"organization_id": organization_id, "workspace_id": workspace_id, "project_id": project_id}

        if collection_exists:
            result_set_collection.insert_one(
                {
                    "organization_id": organization_id,
                    "workspace_id": workspace_id,
                    "project_id": project_id,
                    "name": "dummy_result_set",
                }
            )
            model_test_result_collection.insert_one(
                {
                    "organization_id": organization_id,
                    "workspace_id": workspace_id,
                    "project_id": project_id,
                    "name": "dummy_model_test_result",
                }
            )
            assert result_set_collection.count_documents(filter_query) == 1
            assert model_test_result_collection.count_documents(filter_query) == 1

        RemoveResultSetAndModelTestResultMigration.upgrade_project(
            organization_id=str(organization_id), workspace_id=str(workspace_id), project_id=str(project_id)
        )

        assert result_set_collection.count_documents(filter_query) == 0
        assert model_test_result_collection.count_documents(filter_query) == 0
