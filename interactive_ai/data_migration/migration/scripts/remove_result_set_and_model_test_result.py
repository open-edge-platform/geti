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

import logging
from uuid import UUID

from bson import ObjectId
from pymongo.collection import Collection

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


RESULT_SET = "result_set"
MODEL_TEST_RESULT = "model_test_result"


class RemoveResultSetAndModelTestResultMigration(IMigrationScript):
    @classmethod
    def upgrade_non_project_data(cls) -> None:
        """Delete all documents in 'result_set' and 'model_test_result' collections."""
        db = MongoDBConnection().geti_db
        result_set_collection = db.get_collection(RESULT_SET)
        model_test_result_collection = db.get_collection(MODEL_TEST_RESULT)
        cls._delete_all(collection=result_set_collection, query={})
        cls._delete_all(collection=model_test_result_collection, query={})

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """Delete all documents from the 'result_set' and 'model_test_result' collections contained in a project."""
        db = MongoDBConnection().geti_db
        preliminary_filter_query = {
            "organization_id": UUID(organization_id),
            "workspace_id": UUID(workspace_id),
            "project_id": ObjectId(project_id),
        }
        result_set_collection = db.get_collection(RESULT_SET)
        model_test_result_collection = db.get_collection(MODEL_TEST_RESULT)
        cls._delete_all(collection=result_set_collection, query=preliminary_filter_query)
        cls._delete_all(collection=model_test_result_collection, query=preliminary_filter_query)

    @staticmethod
    def _delete_all(collection: Collection, query: dict) -> None:
        """Delete all documents from the collection that match the query."""
        result = collection.delete_many(query)
        if result.deleted_count > 0:
            logger.info(f"Deleted {result.deleted_count} documents from collection '{collection.name}'.")

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """No action required"""

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        """No action required"""
