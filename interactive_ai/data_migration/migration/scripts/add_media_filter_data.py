# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from uuid import UUID

from bson import ObjectId
from pymongo.collection import Collection

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


class AddDataForFilteringMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """
        Add additional media data, like size and video frame info, to dataset filtering collections
        """
        db = MongoDBConnection().geti_db
        dataset_storage_filter_collection = db.get_collection("dataset_storage_filter_data")
        training_revision_collection = db.get_collection("training_revision_filter")
        image_collection = db.get_collection("image")
        video_collection = db.get_collection("video")
        preliminary_filter = {
            "project_id": ObjectId(project_id),
            "workspace_id": UUID(workspace_id),
            "organization_id": UUID(organization_id),
        }

        cls._add_filter_data_for_collection(
            filter_collection=dataset_storage_filter_collection,
            image_collection=image_collection,
            video_collection=video_collection,
            preliminary_filter=preliminary_filter,
        )
        cls._add_filter_data_for_collection(
            filter_collection=training_revision_collection,
            image_collection=image_collection,
            video_collection=video_collection,
            preliminary_filter=preliminary_filter,
        )

    @classmethod
    def _add_filter_data_for_collection(
        cls,
        filter_collection: Collection,
        image_collection: Collection,
        video_collection: Collection,
        preliminary_filter: dict,
    ) -> None:
        docs = filter_collection.find(
            {
                **preliminary_filter,
                "size": {"$exists": False},
            }
        )
        for filter_doc in docs:
            if filter_doc["media_identifier"]["type"] == "image":
                image_doc = image_collection.find_one(
                    {
                        **preliminary_filter,
                        "_id": filter_doc["media_identifier"]["media_id"],
                    }
                )
                if image_doc is None:
                    logger.warning(
                        "Cannot find image for image with image id %s in project %s",
                        filter_doc["media_identifier"]["media_id"],
                        preliminary_filter,
                    )
                    continue

                update_doc = {
                    "size": image_doc["size"],
                    "uploader_id": image_doc["uploader_id"],
                }
            else:
                video_doc = video_collection.find_one(
                    {
                        **preliminary_filter,
                        "_id": filter_doc["media_identifier"]["media_id"],
                    }
                )
                if video_doc is None:
                    logger.warning(
                        "Cannot find video for video with image id %s in project %s",
                        filter_doc["media_identifier"]["media_id"],
                        preliminary_filter,
                    )
                    continue

                update_doc = {
                    "size": video_doc["size"],
                    "uploader_id": video_doc["uploader_id"],
                    "frame_count": video_doc["total_frames"],
                    "frame_stride": video_doc["stride"],
                    "frame_rate": video_doc["fps"],
                    "duration": int(video_doc["total_frames"] / video_doc["fps"]),
                }

            filter_collection.find_one_and_update(
                filter={
                    **preliminary_filter,
                    "_id": filter_doc["_id"],
                },
                update={"$set": update_doc},
            )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """No action necessary because an extra field in the filter doc does not hinder the backwards mapper"""

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass
