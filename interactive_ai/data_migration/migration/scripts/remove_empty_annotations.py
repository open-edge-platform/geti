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


class RemoveEmptyAnnotationMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        db = MongoDBConnection().geti_db
        annotation_scene_collection = db.get_collection("annotation_scene")
        annotation_scene_collection.update_many(
            filter={
                "annotations.labels": {"$size": 0},
                "project_id": ObjectId(project_id),
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
            },
            update={"$pull": {"annotations": {"labels": {"$eq": []}}}},
        )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """No action required"""

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        """No action required"""

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        """No action required"""
