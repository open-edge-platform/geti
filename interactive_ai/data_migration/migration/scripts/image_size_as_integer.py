# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection


class ImageSizeToIntegerMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        db = MongoDBConnection().geti_db
        images = db.get_collection("image")
        images.update_many(
            {
                "project_id": ObjectId(project_id),
                "workspace_id": UUID(workspace_id),
                "organization_id": UUID(organization_id),
            },
            [{"$set": {"size": {"$toInt": "$size"}}}],
        )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        # no action necessary because ImageToMongo.backward is compatible with both str and int values
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass
