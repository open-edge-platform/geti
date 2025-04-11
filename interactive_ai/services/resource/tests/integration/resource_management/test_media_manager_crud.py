# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
import io

import pytest

from resource_management.media_manager import MediaManager

from geti_fastapi_tools.exceptions import InvalidMediaException
from geti_types import ID
from sc_sdk.entities.media import ImageExtensions, VideoExtensions
from sc_sdk.repos.storage.storage_client import BytesStream


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
