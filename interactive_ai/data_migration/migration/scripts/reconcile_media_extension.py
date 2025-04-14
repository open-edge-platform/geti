# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection

MEDIA_COLLECTION_NAMES = ["image", "video"]

logger = logging.getLogger(__name__)


class ReconcileMediaExtensionMigration(IMigrationScript):
    """
    Migration class to fix values of the 'extension' field that are inconsistent
    with respect to the 'binary_filename' value in the 'image' and 'video' collections.

    The inconsistencies would exist for some media formats because:
      - 'extension' used to be determined from the user-uploaded raw file, before any conversion
      - 'binary_filename' represents the file saved in the object storage, possibly converted for compatibility reasons
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        database = MongoDBConnection().geti_db

        for collection_name in MEDIA_COLLECTION_NAMES:
            logger.info(f"Processing collection: {collection_name}")
            media_collection = database.get_collection(collection_name)
            # only update documents where the extension field is inconsistent with the binary_filename
            media_filter = {
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
                "project_id": ObjectId(project_id),
                "binary_filename": {"$exists": True},
                "$expr": {
                    "$not": {
                        "$regexMatch": {
                            "input": "$binary_filename",
                            "regex": {"$concat": [{"$toString": "$_id"}, ".", {"$toLower": "$extension"}]},
                        }
                    }
                },
            }

            # Derive the right extension from 'binary_filename' (format is of "{_id}.{extension}") and make it uppercase
            update = [
                {"$set": {"extension": {"$toUpper": {"$arrayElemAt": [{"$split": ["$binary_filename", "."]}, -1]}}}}
            ]

            res = media_collection.update_many(filter=media_filter, update=update)

            if res.modified_count:
                logger.info(
                    f"Added extension field to {res.modified_count} {collection_name} documents in project {project_id}"
                )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        # No downgrade action necessary as the new value of the extension field is more accurate than the previous one
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass
