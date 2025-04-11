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

import pymongo.errors
from bson import ObjectId
from pymongo.database import Database

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


CONFIGURABLE_PARAMETERS = "configurable_parameters"
NDR_CONFIG = "ndr_config"
NDR_HASH = "ndr_hash"


class RemoveNDRMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """Removes the "data.use_ndr" field from all configurable_parameters documents in the project"""
        db = MongoDBConnection().geti_db
        configurable_parameters = db.get_collection(CONFIGURABLE_PARAMETERS)
        res = configurable_parameters.update_many(
            {
                "project_id": ObjectId(project_id),
                "workspace_id": UUID(workspace_id),
                "organization_id": UUID(organization_id),
                "data.use_ndr": {"$exists": True},
            },
            [{"$unset": "data.use_ndr"}],
        )
        if res.modified_count:
            logger.info(
                f"Removed `data.use_ndr` field from {res.modified_count} "
                f"{CONFIGURABLE_PARAMETERS} documents in project {project_id}"
            )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """No action required, as the `data.use_ndr` is an optional field"""

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        """Drops the "ndr_config" and "ndr_hash" collections"""
        db = MongoDBConnection().geti_db
        cls._drop_collection(db, collection_name=NDR_CONFIG)
        cls._drop_collection(db, collection_name=NDR_HASH)

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        """Recreates the "ndr_config" and "ndr_hash" collections"""
        db = MongoDBConnection().geti_db
        cls._recreate_collection(db, collection_name=NDR_CONFIG)
        cls._recreate_collection(db, collection_name=NDR_HASH)

    @staticmethod
    def _drop_collection(database: Database, collection_name: str) -> None:
        ret = database.drop_collection(collection_name)
        if ret["ok"]:
            logger.info(f"Dropped collection '{collection_name}'")
        else:
            logger.warning(f"Collection to drop not found: '{collection_name}'")

    @staticmethod
    def _recreate_collection(database: Database, collection_name: str) -> None:
        try:
            # Note: indexes will be recreated dynamically when the collection is accessed
            database.create_collection(collection_name)
        except pymongo.errors.CollectionInvalid:
            logger.warning(f"Attempted to recreate already existing collection: '{collection_name}'")
