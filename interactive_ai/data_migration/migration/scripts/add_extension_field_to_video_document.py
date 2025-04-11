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

DATABASE_NAME = "geti"

logger = logging.getLogger(__name__)


class AddExtensionFieldToVideo(IMigrationScript):
    """
    This script adds and populates the field "extension" for the video documents. This makes it more consistent
    with the image documents.
    If not present already, the extension field is created and populated by extracting the extension
    from the existing property "binary_filename".
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        database = MongoDBConnection().geti_db
        videos_collection = database.get_collection("video")

        # only update documents that do not have the extension field
        filter = {
            "organization_id": UUID(organization_id),
            "workspace_id": UUID(workspace_id),
            "project_id": ObjectId(project_id),
            "extension": {"$exists": False},
        }

        # Extension is extracted from the binary_filename field which is of
        # "{_id}.{extension}" format and is capitalised
        update = [{"$set": {"extension": {"$toUpper": {"$arrayElemAt": [{"$split": ["$binary_filename", "."]}, -1]}}}}]

        res = videos_collection.update_many(filter=filter, update=update)

        if res.modified_count:
            logger.info(f"Added extension field to {res.modified_count} video documents in project {project_id}")

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        # No downgrade action necessary as having an extension field in the documents does
        # not cause incompatibilities
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass
