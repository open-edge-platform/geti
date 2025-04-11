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

from collections.abc import Callable
from functools import partial
from unittest.mock import patch
from uuid import UUID

import mongomock
import pytest
from bson import ObjectId
from pymongo import MongoClient

from migration.scripts.remove_ndr import RemoveNDRMigration
from migration.utils import MongoDBConnection


class TestRemoveNDRMigration:
    def test_upgrade_project(self, request) -> None:
        def cleanup():
            # Remove the documents added during the test
            configurable_parameters.delete_many({})

        database = MongoDBConnection().client["geti"]
        request.addfinalizer(cleanup)
        configurable_parameters = database.get_collection("configurable_parameters")
        organization_id = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
        workspace_id = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
        project_id = ObjectId("66a0faf070cdf6d0b2ec5f93")
        filter_query = {"organization_id": organization_id, "workspace_id": workspace_id, "project_id": project_id}

        configurable_parameters.insert_one(
            {
                "organization_id": organization_id,
                "workspace_id": workspace_id,
                "project_id": project_id,
                "data": {
                    "use_ndr": {
                        "header": "NDR",
                        "value": False,
                    },
                    "minimum_annotation_size": {
                        "header": "Minimum Annotation Size",
                        "value": -1,
                    },
                    "maximum_number_of_annotations": {
                        "header": "Maximum number of Annotations",
                        "value": -1,
                    },
                },
            }
        )
        assert configurable_parameters.count_documents(filter_query) == 1

        RemoveNDRMigration.upgrade_project(
            organization_id=str(organization_id), workspace_id=str(workspace_id), project_id=str(project_id)
        )

        assert configurable_parameters.count_documents(filter_query) == 1
        assert "use_ndr" not in configurable_parameters.find_one(filter_query)["data"]

    @pytest.mark.parametrize("collection_exists", [True, False], ids=["existing", "non-existing"])
    def test_upgrade_non_project_data(self, collection_exists) -> None:
        def drop_collection_with_return(collection_name: str, original_fn: Callable):
            # wrapper around mongomock.Database.drop_collection that returns info, like the pymongo method does
            original_fn(collection_name)
            return {"ok": 1.0}

        mock_db = mongomock.MongoClient(uuidRepresentation="standard").db
        if collection_exists:
            mock_db.create_collection("ndr_config")
            mock_db.create_collection("ndr_hash")
            assert "ndr_config" in mock_db.list_collection_names()
            assert "ndr_hash" in mock_db.list_collection_names()
        else:
            assert "ndr_config" not in mock_db.list_collection_names()
            assert "ndr_hash" not in mock_db.list_collection_names()

        with (
            patch.object(MongoClient, "get_database", return_value=mock_db),
            patch.object(
                mock_db,
                "drop_collection",
                new=partial(drop_collection_with_return, original_fn=mock_db.drop_collection),
            ),
        ):
            RemoveNDRMigration.upgrade_non_project_data()

        assert "ndr_config" not in mock_db.list_collection_names()
        assert "ndr_hash" not in mock_db.list_collection_names()

    @pytest.mark.parametrize("collection_exists", [True, False], ids=["existing", "non-existing"])
    def test_downgrade_non_project_data(self, collection_exists) -> None:
        mock_db = mongomock.MongoClient(uuidRepresentation="standard").db
        if collection_exists:
            mock_db.create_collection("ndr_config")
            mock_db.create_collection("ndr_hash")
            assert "ndr_config" in mock_db.list_collection_names()
            assert "ndr_hash" in mock_db.list_collection_names()
        else:
            assert "ndr_config" not in mock_db.list_collection_names()
            assert "ndr_hash" not in mock_db.list_collection_names()

        with patch.object(MongoClient, "get_database", return_value=mock_db):
            RemoveNDRMigration.downgrade_non_project_data()

        assert "ndr_config" in mock_db.list_collection_names()
        assert "ndr_hash" in mock_db.list_collection_names()
