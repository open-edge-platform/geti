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

from http import HTTPStatus
from unittest.mock import patch

from testfixtures import compare

from communication.rest_controllers.annotation_controller import LATEST, AnnotationRESTController

from geti_types import ID, DatasetStorageIdentifier, ImageIdentifier, VideoFrameIdentifier

DUMMY_ORGANIZATION_ID = "6682a33b-3d18-4dab-abee-f797090480e0"
DUMMY_ANNOTATION_ID = "a23456789012345678900000"
DUMMY_DATA = {"dummy_key": "dummy_value"}
DUMMY_DATASET_ID = "012345678901234567890000"
DUMMY_FRAME_INDEX = "123"
DUMMY_IMAGE_ID = "123456789012345678900000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_USER = ID("dummy_user")
DUMMY_VIDEO_ID = "456789012345678901230000"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_INVALID_PARAM = "invalid_param_123"
DUMMY_DATASET_STORAGE_IDENTIFIER = DatasetStorageIdentifier(
    workspace_id=ID(DUMMY_WORKSPACE_ID),
    project_id=ID(DUMMY_PROJECT_ID),
    dataset_storage_id=ID(DUMMY_DATASET_ID),
)

API_BASE_PATTERN = (
    f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
    f"/workspaces/{DUMMY_WORKSPACE_ID}"
    f"/projects/{DUMMY_PROJECT_ID}"
    f"/datasets/{DUMMY_DATASET_ID}"
)
API_IMAGE_PATTERN = f"{API_BASE_PATTERN}/media/images"
API_VIDEO_PATTERN = f"{API_BASE_PATTERN}/media/videos"

ERROR_CODE = "not_implemented_error_rest"
ERROR_MESSAGE = "It is not supported to edit an annotation on an ROI"


class TestAnnotationRESTEndpoint:
    def test_media_image_annotations_endpoint_post(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_IMAGE_PATTERN}/{DUMMY_IMAGE_ID}/annotations"

        # Act
        with patch.object(
            AnnotationRESTController,
            "make_image_annotation",
            return_value=DUMMY_DATA,
        ) as mock_make_anno:
            result = fxt_resource_rest.post(endpoint, json=DUMMY_DATA)

        # Assert
        mock_make_anno.assert_called_once_with(
            data=DUMMY_DATA,
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            image_id=ID(DUMMY_IMAGE_ID),
            user_id=DUMMY_USER,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_image_annotation_endpoint_get(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_IMAGE_PATTERN}/{DUMMY_IMAGE_ID}/annotations/{DUMMY_ANNOTATION_ID}"
        media_identifier = ImageIdentifier(image_id=ID(DUMMY_IMAGE_ID))

        # Act
        with patch.object(
            AnnotationRESTController,
            "get_annotation",
            return_value=DUMMY_DATA,
        ) as mock_get_anno:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_anno.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            annotation_id=ID(DUMMY_ANNOTATION_ID),
            media_identifier=media_identifier,
            label_only=False,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_image_annotation_endpoint_invalid_parameter(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = (
            f"{API_IMAGE_PATTERN}/{DUMMY_IMAGE_ID}/annotations/{DUMMY_ANNOTATION_ID}?label_only={DUMMY_INVALID_PARAM}"
        )

        # Act and Assert
        response = fxt_resource_rest.get(endpoint)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_media_video_annotations_endpoint_post(self, fxt_resource_rest):
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/frames/{DUMMY_FRAME_INDEX}/annotations"

        # Act
        with patch.object(
            AnnotationRESTController,
            "make_video_frame_annotation",
            return_value=DUMMY_DATA,
        ) as mock_make_anno:
            result = fxt_resource_rest.post(endpoint, json=DUMMY_DATA)

        # Assert
        mock_make_anno.assert_called_once_with(
            data=DUMMY_DATA,
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            video_id=DUMMY_VIDEO_ID,
            frame_index=int(DUMMY_FRAME_INDEX),
            user_id=DUMMY_USER,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_video_annotation_endpoint_get(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/annotations/latest"

        # Act
        with patch.object(
            AnnotationRESTController,
            "get_video_frame_annotations",
            return_value=DUMMY_DATA,
        ) as mock_get_annos:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_annos.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
            video_id=ID(DUMMY_VIDEO_ID),
            annotation_id=ID(LATEST),
            label_only=False,
            start_frame=None,
            end_frame=None,
            frameskip=1,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_video_annotation_endpoint_invalid_parameter(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/annotations/latest?label_only={DUMMY_INVALID_PARAM}"

        # Act and Assert
        response = fxt_resource_rest.get(endpoint)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_video_range_annotation_endpoint_get(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/range_annotation"

        # Act
        with patch.object(
            AnnotationRESTController,
            "get_video_range_annotation",
            return_value=DUMMY_DATA,
        ) as mock_get_video_range_annos:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_video_range_annos.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            video_id=ID(DUMMY_VIDEO_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_video_range_annotation_endpoint_post(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/range_annotation?skip_frame=3"

        # Act
        with patch.object(
            AnnotationRESTController,
            "make_video_range_annotation",
            return_value=DUMMY_DATA,
        ) as mock_make_video_range_anno:
            result = fxt_resource_rest.post(endpoint, json=DUMMY_DATA)

        # Assert
        mock_make_video_range_anno.assert_called_once_with(
            video_annotation_range_data=DUMMY_DATA,
            dataset_storage_identifier=DatasetStorageIdentifier(
                workspace_id=ID(DUMMY_WORKSPACE_ID),
                project_id=ID(DUMMY_PROJECT_ID),
                dataset_storage_id=ID(DUMMY_DATASET_ID),
            ),
            video_id=ID(DUMMY_VIDEO_ID),
            user_id=DUMMY_USER,
            skip_frame=3,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_video_frame_annotation_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/frames/{DUMMY_FRAME_INDEX}/annotations/{DUMMY_ANNOTATION_ID}"
        dummy_video_frame_identifier = VideoFrameIdentifier(ID(DUMMY_VIDEO_ID), int(DUMMY_FRAME_INDEX))

        # Act
        with patch.object(
            AnnotationRESTController,
            "get_annotation",
            return_value=DUMMY_DATA,
        ) as mock_get_annotation:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_annotation.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            annotation_id=ID(DUMMY_ANNOTATION_ID),
            media_identifier=dummy_video_frame_identifier,
            label_only=False,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_video_frame_annotation_endpoint_invalid_parameter(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = (
            f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/frames/{DUMMY_FRAME_INDEX}/"
            f"annotations/{DUMMY_ANNOTATION_ID}?label_only={DUMMY_INVALID_PARAM}"
        )

        # Act and Assert
        response = fxt_resource_rest.get(endpoint)
        assert response.status_code == HTTPStatus.BAD_REQUEST
