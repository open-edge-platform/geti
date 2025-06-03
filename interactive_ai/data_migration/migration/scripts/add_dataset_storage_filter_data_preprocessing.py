# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


class AddDatasetStorageFilterPreprocessingMigration(IMigrationScript):
    """
    Migration class to handle adding of the 'preprocessing' field to dataset storage filter data
    (collection: dataset_storage_filter_data) docs in the project.
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        database = MongoDBConnection().geti_db

        collection = database.get_collection("dataset_storage_filter_data")
        # only update documents that do not have the extension field
        media_filter = {
            "organization_id": UUID(organization_id),
            "workspace_id": UUID(workspace_id),
            "project_id": ObjectId(project_id),
            "preprocessing": {"$exists": False},
        }

        # Add the field named 'preprocessing' to the documents
        update = [{"$set": {"preprocessing": "FINISHED"}}]
        res = collection.update_many(filter=media_filter, update=update)
        if res.modified_count:
            logger.info(
                f"Added preprocessing field to {res.modified_count} "
                "dataset_storage_filter_data documents in project {project_id}"
            )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        # When downgrading projects, the 'preprocessing' field is removed from the documents.
        database = MongoDBConnection().geti_db

        collection = database.get_collection("dataset_storage_filter_data")
        media_filter = {
            "organization_id": UUID(organization_id),
            "workspace_id": UUID(workspace_id),
            "project_id": ObjectId(project_id),
        }
        update = [{"$unset": "preprocessing"}]

        res = collection.update_many(filter=media_filter, update=update)
        if res.modified_count:
            logger.info(
                f"Removed preprocessing field from {res.modified_count} "
                "dataset_storage_filter_data documents in project {project_id}"
            )

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass
