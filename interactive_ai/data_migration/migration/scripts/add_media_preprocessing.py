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
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection

COLLECTION_UPDATES = {
    "image": {"status": "FINISHED"},
    "video": {"status": "FINISHED"},
    "dataset_storage_filter": "FINISHED",
}

logger = logging.getLogger(__name__)


class AddMediaPreprocessingMigration(IMigrationScript):
    """
    Migration class to handle adding of the 'preprocessing' field to image (collection: image),
    video (collection: video) and dataset storage filter (collection: dataset_storage_filter) docs in the project.
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        database = MongoDBConnection().geti_db

        for collection_name, preprocessing in COLLECTION_UPDATES.items():
            collection = database.get_collection(collection_name)
            # only update documents that do not have the extension field
            media_filter = {
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
                "project_id": ObjectId(project_id),
                "preprocessing": {"$exists": False},
            }

            # Add the field named 'preprocessing' to the documents
            update = [{"$set": {"preprocessing": preprocessing}}]
            res = collection.update_many(filter=media_filter, update=update)
            if res.modified_count:
                logger.info(
                    f"Added preprocessing field to {res.modified_count} "
                    f"{collection_name} documents in project {project_id}"
                )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        # When downgrading projects, the 'preprocessing' field is removed from the documents.
        database = MongoDBConnection().geti_db
        for collection_name, _ in COLLECTION_UPDATES.items():
            media_collection = database.get_collection(collection_name)
            media_filter = {
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
                "project_id": ObjectId(project_id),
            }
            update = [{"$unset": "preprocessing"}]

            res = media_collection.update_many(filter=media_filter, update=update)
            if res.modified_count:
                logger.info(
                    f"Removed preprocessing field from {res.modified_count} "
                    f"{collection_name} documents in project {project_id}"
                )

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass
