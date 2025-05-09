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
import tempfile
from typing import TYPE_CHECKING

import cv2
import numpy as np
from behave import given, when
from behave.runner import Context

if TYPE_CHECKING:
    from geti_client import MediaApi
from PIL import Image

logger = logging.getLogger(__name__)


def _create_and_upload_random_image(context: Context, image_name: str) -> None:
    random_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(random_image)

    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = f"{temp_dir}/{image_name}"
        img.save(image_path)

        media_api: MediaApi = context.media_api

        upload_image_response = media_api.upload_image(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            dataset_id=context.dataset_id,
            file=image_path,  # file.read(),
            _headers={"Content-Disposition": f'form-data; name="file"; filename="{image_name}"'},
        )

        context._media_info_by_name[image_name] = upload_image_response


def _create_and_upload_random_video(context: Context, video_name: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = f"{temp_dir}/{video_name}"

        try:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
            video_writer = cv2.VideoWriter(video_path, fourcc, 1.0, (100, 100))

            # Generate 20 random frames
            for _ in range(20):
                frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
                video_writer.write(frame)
        finally:
            video_writer.release()

        media_api: MediaApi = context.media_api

        upload_video_response = media_api.upload_video(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            dataset_id=context.dataset_id,
            file=video_path,
            _headers={"Content-Disposition": f'form-data; name="file"; filename="{video_name}"'},
        )

        context._media_info_by_name[video_name] = upload_video_response


@given("an image called '{image_name}'")
def step_given_image_with_custom_name(context: Context, image_name: str) -> None:
    _create_and_upload_random_image(context=context, image_name=image_name)


@given("a video called '{video_name}'")
def step_given_video_with_custom_name(context: Context, video_name: str) -> None:
    _create_and_upload_random_video(context=context, video_name=video_name)


@when("the user loads the image '{image_name}'")
def step_when_user_loads_image(context: Context, image_name: str) -> None:
    media_api: MediaApi = context.media_api
    context._media_info_by_name[image_name] = media_api.get_image_detail(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        dataset_id=context.dataset_id,
        image_id=context._media_info_by_name[image_name].id,
    )


@when("the user tries to load the image '{image_name}'")
def step_when_user_tries_loading_image(context: Context, image_name: str) -> None:
    try:
        step_when_user_loads_image(context=context, image_name=image_name)
    except Exception as e:
        context.exception = e
