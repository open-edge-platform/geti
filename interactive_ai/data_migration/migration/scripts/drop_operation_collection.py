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

import logging

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


class DropOperationCollectionMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        """
        Remove old operation collection that is no longer in use
        """
        db = MongoDBConnection().geti_db
        # Drop the operation collection, returns True even if collection does not exist
        db.drop_collection("operation")

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        """No action required, indexes are automatically recreated by the repos"""
