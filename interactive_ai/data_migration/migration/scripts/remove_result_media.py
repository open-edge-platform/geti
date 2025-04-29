# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os

from migration.utils import IMigrationScript, MongoDBConnection
from migration.utils.connection import MinioStorageClient

BUCKET_NAME_RESULT_MEDIA = os.environ.get("BUCKET_NAME_RESULT_MEDIA", "resultmedia")


class RemoveResultMediaMigration(IMigrationScript):
    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        storage_prefix = f"/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
        cls.delete_result_media_from_storage(prefix=storage_prefix)
        project_filter = {"project_id": project_id}
        cls.delete_result_media_from_db(additional_filter=project_filter)

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        cls.delete_result_media_from_storage()
        cls.delete_result_media_from_db()

    @staticmethod
    def delete_result_media_from_db(additional_filter: dict | None = None) -> None:
        """
        Deletes all the result media from the metadata_item collection in the database. The result media documents are
        identifiable by matching on content.schema == result_media
        """
        db = MongoDBConnection().geti_db
        metadata_collection = db.get_collection("metadata_item")
        result_media_filter = {"content.schema": "result_media"}
        if additional_filter:
            result_media_filter |= additional_filter
        metadata_collection.delete_many(filter=result_media_filter)

    @staticmethod
    def delete_result_media_from_storage(prefix: str | None = None) -> None:
        """
        Deletes all result media binaries from the storage. There is a bucket specifically for the result media so the
        bucket is first emptied recursively and then deleted.
        """
        storage_client = MinioStorageClient().client
        if storage_client.bucket_exists(BUCKET_NAME_RESULT_MEDIA):
            result_media_objects = storage_client.list_objects(
                bucket_name=BUCKET_NAME_RESULT_MEDIA, recursive=True, prefix=prefix
            )
            for result_media in result_media_objects:
                storage_client.remove_object(bucket_name=BUCKET_NAME_RESULT_MEDIA, object_name=result_media.object_name)
            if prefix is None:
                storage_client.remove_bucket(BUCKET_NAME_RESULT_MEDIA)
