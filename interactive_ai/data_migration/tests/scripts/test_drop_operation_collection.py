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

from unittest.mock import patch

import mongomock
from bson import ObjectId
from pymongo import MongoClient

from migration.scripts.drop_operation_collection import DropOperationCollectionMigration


class TestDropOperationCollectionMigration:
    def test_remove_index_from_annotation_scene(self) -> None:
        # Arrange
        mock_db = mongomock.MongoClient().db
        collection = mock_db.get_collection("operation")
        doc = {
            "_id": ObjectId("66a360141ad051b7b6ab1939"),
            "project_id": ObjectId("66a0faf070cdf6d0b2ec5f93"),
        }
        collection.insert_one(doc)
        assert "operation" in mock_db.list_collection_names()
        assert list(collection.find({}))

        # Act
        with patch.object(MongoClient, "get_database", return_value=mock_db):
            DropOperationCollectionMigration.upgrade_non_project_data()

        # Assert
        assert "operation" not in mock_db.list_collection_names()
        assert DropOperationCollectionMigration.upgrade_non_project_data() is None
        collection = mock_db.get_collection("operation")
        assert not list(collection.find({}))
