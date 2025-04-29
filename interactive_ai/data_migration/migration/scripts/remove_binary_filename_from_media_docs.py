# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection

MEDIA_COLLECTION_NAMES = ["image", "video"]

logger = logging.getLogger(__name__)


class RemoveBinaryFilenameFromMediaDocsMigration(IMigrationScript):
    """
    Migration class to handle the removal of the 'binary_filename' field from the image (collection: image)
    and video (collection: video) docs in the project.
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        database = MongoDBConnection().geti_db

        for collection_name in MEDIA_COLLECTION_NAMES:
            media_collection = database.get_collection(collection_name)
            # only update documents that do not have the extension field
            media_filter = {
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
                "project_id": ObjectId(project_id),
                "binary_filename": {"$exists": True},
            }

            # Remove the field named 'binary_filename' from the documents
            update = [{"$unset": "binary_filename"}]
            res = media_collection.update_many(filter=media_filter, update=update)
            if res.modified_count:
                logger.info(
                    f"Removed binary_filename field from {res.modified_count} "
                    f"{collection_name} documents in project {project_id}"
                )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        # When downgrading projects, the 'binary_filename' field is added back to the media documents.
        database = MongoDBConnection().geti_db
        for collection_name in MEDIA_COLLECTION_NAMES:
            media_collection = database.get_collection(collection_name)
            media_filter = {
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
                "project_id": ObjectId(project_id),
                "binary_filename": {"$exists": False},
            }
            # Binary file name is constructed using the _id and the extension
            # binary_filename = f"{_id}.{extension.lower()}"
            update = [
                {
                    "$set": {
                        "binary_filename": {
                            "$concat": [
                                {"$toString": "$_id"},
                                ".",
                                {"$toLower": "$extension"},
                            ]
                        }
                    }
                }
            ]

            res = media_collection.update_many(filter=media_filter, update=update)
            if res.modified_count:
                logger.info(
                    f"Added binary_filename field to {res.modified_count} "
                    f"{collection_name} documents in project {project_id}"
                )

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass
