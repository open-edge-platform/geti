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
import os

from minio.commonconfig import CopySource

from migration.utils import IMigrationScript
from migration.utils.connection import MinioStorageClient

logger = logging.getLogger(__name__)

BUCKET_NAME_IMAGES = os.environ.get("BUCKET_NAME_IMAGES", "images")
BUCKET_NAME_VIDEOS = os.environ.get("BUCKET_NAME_VIDEOS", "videos")


class SanitizeMediaBinaryExtensionMigration(IMigrationScript):
    """
    This migration script is responsible for sanitizing the media binary extension from the storage by converting all
    the uppercase extensions to lowercase.
    """

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        # Migration on single project is not required
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        cls._sanitize_media_from_storage(bucket=BUCKET_NAME_IMAGES)
        cls._sanitize_media_from_storage(bucket=BUCKET_NAME_VIDEOS)

    @staticmethod
    def _sanitize_media_from_storage(bucket: str, prefix: str | None = None) -> None:
        """
        Sanitize the media binary extension from the storage by converting all the uppercase extensions to lowercase.

        :param bucket: The bucket name where the media objects are stored.
        :param prefix: The prefix to filter the media objects.
        """
        sanitized_media = 0
        storage_client = MinioStorageClient().client
        if storage_client.bucket_exists(bucket):
            media_objects = storage_client.list_objects(bucket_name=bucket, recursive=True, prefix=prefix)
            for media in media_objects:
                name, extension = os.path.splitext(media.object_name)
                if extension.isupper():
                    # copy the object with the new name and remove the object with old name
                    storage_client.copy_object(
                        bucket,
                        f"{name}.{extension.lower()}",
                        CopySource(bucket, media.object_name),
                    )
                    storage_client.remove_object(bucket_name=bucket, object_name=media.object_name)
                    sanitized_media += 1
        logger.info(f"Sanitized extensions of {sanitized_media} {bucket} from binary storage")
