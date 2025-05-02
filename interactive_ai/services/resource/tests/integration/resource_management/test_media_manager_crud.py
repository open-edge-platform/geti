# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import io

import pytest

from resource_management.media_manager import MediaManager

from geti_fastapi_tools.exceptions import InvalidMediaException
from geti_types import ID
from iai_core.entities.media import ImageExtensions, VideoExtensions
from iai_core.repos.storage.storage_client import BytesStream


class TestIntegrationMediaManager:
    def test_upload_empty_files(self, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        To test zero byte files.

        <b>Input data:</b>
        A project with no videos or images.

        <b>Expected results:</b>
        Test passes if an exception is raised while uploading a video and image file of zero bytes.

        <b>Steps</b>
        1. Create an instance of the MediaManager.
        2. Check if exception is raised while uploading a video file of zero bytes
        3. Check if exception is raised while uploading an image file of zero bytes
        """
        project = fxt_db_project_service.create_empty_project()
        media_manager = MediaManager()
        dataset_storage = project.get_training_dataset_storage()
        with pytest.raises(InvalidMediaException):
            media_manager.upload_video(
                dataset_storage_identifier=dataset_storage.identifier,
                basename="Zero byte video",
                extension=VideoExtensions.MP4,
                data_stream=BytesStream(data=io.BytesIO(b""), length=0),
                user_id=ID("dummy_user"),
            )
        with pytest.raises(InvalidMediaException):
            media_manager.upload_image(
                dataset_storage_identifier=dataset_storage.identifier,
                basename="Zero byte image",
                extension=ImageExtensions.JPG,
                data_stream=BytesStream(data=io.BytesIO(b""), length=0),
                user_id=ID("dummy_user"),
            )
