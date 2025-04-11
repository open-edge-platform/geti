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
from collections import defaultdict
from typing import Any
from uuid import UUID

from bson import ObjectId
from pymongo.collection import Collection

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


class AddMediaExtensionToFilterDataMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """
        Add media_extension to filter data docs representing the extension from the image and video repo

        This field is necessary to return the correct extension of files to the user
        """
        db = MongoDBConnection().geti_db
        dataset_storage_filter_collection = db.get_collection("dataset_storage_filter_data")
        training_revision_filter_collection = db.get_collection("training_revision_filter")

        image_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "project_id": ObjectId(project_id),
                    "workspace_id": UUID(workspace_id),
                    "organization_id": UUID(organization_id),
                    "media_extension": {"$exists": False},
                    "media_identifier.type": "image",
                },
            },
            {
                "$lookup": {
                    "from": "image",
                    "localField": "media_identifier.media_id",
                    "foreignField": "_id",
                    "as": "image",
                    "pipeline": [
                        {
                            "$match": {
                                "project_id": ObjectId(project_id),
                                "workspace_id": UUID(workspace_id),
                                "organization_id": UUID(organization_id),
                            },
                        },
                        {
                            "$project": {
                                "media_extension": "$extension",
                            },
                        },
                    ],
                },
            },
            {
                "$set": {
                    "media_extension": {"$first": "$image.media_extension"},
                },
            },
        ]

        video_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "project_id": ObjectId(project_id),
                    "workspace_id": UUID(workspace_id),
                    "organization_id": UUID(organization_id),
                    "media_extension": {"$exists": False},
                    "media_identifier.type": {"$in": ["video", "video_frame"]},
                },
            },
            {
                "$lookup": {
                    "from": "video",
                    "localField": "media_identifier.media_id",
                    "foreignField": "_id",
                    "as": "video",
                    "pipeline": [
                        {
                            "$project": {
                                "media_extension": "$extension",
                            },
                        },
                    ],
                },
            },
            {
                "$set": {
                    "media_extension": {"$first": "$video.media_extension"},
                },
            },
        ]

        # Set media_extension in image filter docs
        logger.info("Running set_media_extensions on dataset storage filter collection for images")
        AddMediaExtensionToFilterDataMigration._set_media_extension(
            collection=dataset_storage_filter_collection,
            pipeline=image_pipeline,
            default_extension="PNG",
            project_id=project_id,
            workspace_id=workspace_id,
            organization_id=organization_id,
        )
        logger.info("Running set_media_extensions on training revision filter collection for images")
        AddMediaExtensionToFilterDataMigration._set_media_extension(
            collection=training_revision_filter_collection,
            pipeline=image_pipeline,
            default_extension="PNG",
            project_id=project_id,
            workspace_id=workspace_id,
            organization_id=organization_id,
        )

        # Set media_extension in video filter docs
        logger.info("Running set_media_extensions on dataset storage filter collection for videos")
        AddMediaExtensionToFilterDataMigration._set_media_extension(
            collection=dataset_storage_filter_collection,
            pipeline=video_pipeline,
            default_extension="MP4",
            project_id=project_id,
            workspace_id=workspace_id,
            organization_id=organization_id,
        )
        logger.info("Running set_media_extensions on training revision filter collection for videos")
        AddMediaExtensionToFilterDataMigration._set_media_extension(
            collection=training_revision_filter_collection,
            pipeline=video_pipeline,
            default_extension="MP4",
            project_id=project_id,
            workspace_id=workspace_id,
            organization_id=organization_id,
        )

    @staticmethod
    def _set_media_extension(
        pipeline: list,
        collection: Collection,
        default_extension: str,
        project_id: str,
        workspace_id: str,
        organization_id: str,
    ) -> None:
        docs = collection.aggregate(pipeline=pipeline, allowDiskUse=True)

        result = defaultdict(list)
        for doc in docs:
            media_extension = doc.get("media_extension", default_extension)
            result[media_extension].append(doc["_id"])

        for extension, doc_ids in result.items():
            for batch in range(0, len(doc_ids), 100):
                logger.info(
                    "Setting extension to %s in a batch of 100 documents starting at index %s", extension, batch
                )
                filter = {
                    "project_id": ObjectId(project_id),
                    "workspace_id": UUID(workspace_id),
                    "organization_id": UUID(organization_id),
                    "_id": {"$in": doc_ids[batch : batch + 100]},
                }
                collection.update_many(filter=filter, update=[{"$set": {"media_extension": extension}}])

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """No action necessary because an extra field in the filter docs does not hinder the backwards mapper"""

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass
