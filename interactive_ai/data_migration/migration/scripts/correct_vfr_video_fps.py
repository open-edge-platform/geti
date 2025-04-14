# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
import logging
import os
import subprocess

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection
from migration.utils.connection import MinioStorageClient

logger = logging.getLogger(__name__)

BUCKET_NAME_VIDEOS = os.environ.get("BUCKET_NAME_VIDEOS", "videos")


class CorrectVFRVideoFPS(IMigrationScript):
    """
    Script that reloads each video and gets the FPS using ffprobe. If the FPS does not match with the value that is set
    in the database, it will be updated.
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        db = MongoDBConnection().geti_db
        storage_client = MinioStorageClient().client
        storage_prefix = f"organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"

        video_collection = db.get_collection("video")
        dataset_storage_collection = db.get_collection("dataset_storage")

        dataset_storages = dataset_storage_collection.find({"project_id": ObjectId(project_id)})
        for dataset_storage in dataset_storages:
            dataset_storage_id = dataset_storage["_id"]
            videos = video_collection.find({"dataset_storage_id": dataset_storage_id})
            ds_storage_prefix = f"{storage_prefix}/dataset_storages/{dataset_storage_id}"
            for video in videos:
                video_id = video["_id"]
                video_extension = video["extension"]
                video_path = f"{ds_storage_prefix}/{video_id}.{video_extension.lower()}"
                fps = video["fps"]
                try:
                    url = storage_client.presigned_get_object(BUCKET_NAME_VIDEOS, video_path)
                    new_fps = cls.get_video_fps(url)
                except Exception as e:
                    logger.warning(f"Failed to get video FPS for video {video_id}: {e}")
                    continue
                if new_fps != fps:
                    video_collection.update_one({"_id": video_id}, {"$set": {"fps": new_fps}})
                    logger.info(f"Updated FPS for video {video_id} from {fps} to {new_fps}")

    @staticmethod
    def get_video_fps(video_path: str) -> float:
        # Run ffprobe to get video stream information
        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=r_frame_rate",
                "-of",
                "json",
                video_path,
            ],
            capture_output=True,
            check=False,
        )
        ffprobe_output = json.loads(result.stdout)
        r_frame_rate = ffprobe_output["streams"][0]["r_frame_rate"]
        num, denominator = map(int, r_frame_rate.split("/"))
        return num / denominator

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass
