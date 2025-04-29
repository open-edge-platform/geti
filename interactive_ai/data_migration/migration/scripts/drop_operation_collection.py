# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
