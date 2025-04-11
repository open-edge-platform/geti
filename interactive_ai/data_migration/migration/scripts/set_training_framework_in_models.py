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

DEFAULT_TRAINING_FRAMEWORK = {"type": "OTX", "version": "1.6.2"}

logger = logging.getLogger(__name__)


class SetTrainingFrameworkInModelsMigration(IMigrationScript):
    """
    This script updates "model" documents by adding a field 'training_framework' if it doesn't exist.
    The value is a default one, which assumes that all existing models are compatible with OTX 1.6.2.
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        db = MongoDBConnection().geti_db
        model_collection = db.get_collection("model")
        res = model_collection.update_many(
            {
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
                "project_id": ObjectId(project_id),
                "training_framework": {"$exists": False},
            },
            {"$set": {"training_framework": DEFAULT_TRAINING_FRAMEWORK}},
        )
        logger.info(f"Updated {res.modified_count} model documents in project '{project_id}'")

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        # no action necessary: the presence of the new field does not cause incompatibilities with previous versions
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass
