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

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


class AddModelPurgeInfoMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """
        Adds model purge information to the model entries in the DB
        """
        db = MongoDBConnection().geti_db
        model_collection = db.get_collection("model")
        model_collection.update_many(
            {
                "project_id": ObjectId(project_id),
                "workspace_id": UUID(workspace_id),
                "organization_id": UUID(organization_id),
                "purge_info": {"$exists": False},
            },
            [{"$set": {"purge_info": {"is_purged": False}}}],
        )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """No action necessary"""

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass
