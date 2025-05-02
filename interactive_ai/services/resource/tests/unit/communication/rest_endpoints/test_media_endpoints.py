# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import io
import os
import tempfile
import uuid
from http import HTTPStatus
from pathlib import Path
from unittest.mock import ANY, patch

import cv2
import numpy as np
import pytest
from PIL import Image
from starlette import status
from testfixtures import compare

from communication.constants import MAX_N_MEDIA_RETURNED
from communication.rest_controllers import MediaRESTController
from usecases.dataset_filter import DatasetFilter, DatasetFilterField, DatasetFilterSortDirection

from geti_fastapi_tools.exceptions import BadRequestException
from geti_types import ID, DatasetStorageIdentifier
from iai_core_py.repos import BinaryRepo

DUMMY_DATA = {"dummy_key": "dummy_value"}
DUMMY_DATASET_ID = "012345678901234567890000"
DUMMY_FRAME_INDEX = "123"
DUMMY_IMAGE_ID = "123456789012345678900000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_USER = ID("dummy_user")
DUMMY_MEDIA_DATA = "media_query_data"
DUMMY_VIDEO_ID = "456789012345678901230000"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_ORGANIZATION_ID = "6682a33b-3d18-4dab-abee-f797090480e0"
DUMMY_DATASET_STORAGE_IDENTIFIER = DatasetStorageIdentifier(
    workspace_id=ID(DUMMY_WORKSPACE_ID),
    project_id=ID(DUMMY_PROJECT_ID),
    dataset_storage_id=ID(DUMMY_DATASET_ID),
)
DUMMY_FILES = {"files": 123}
DUMMY_REST_MEDIA = {"media": "dummy_rest_media"}

API_BASE_PATTERN = (
    f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}/workspaces/{DUMMY_WORKSPACE_ID}"
    f"/projects/{DUMMY_PROJECT_ID}"
    f"/datasets/{DUMMY_DATASET_ID}"
)
API_IMAGE_PATTERN = f"{API_BASE_PATTERN}/media/images"
API_VIDEO_PATTERN = f"{API_BASE_PATTERN}/media/videos"

ERROR_CODE = "user_error"
ERROR_MESSAGE = "User cannot be found"

FULL = "full"
IMAGE = "image"
LABELS = "labels"
STREAM = "stream"
THUMB = "thumb"
THUMB_STREAM = "thumb_stream"
VIDEO = "video"
HEADERS = {"Content-Type": "application/json"}


@pytest.fixture
def fxt_random_image_file():
    random_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(random_image)
    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = f"{temp_dir}/crate.png"
        img.save(image_path)
        yield image_path


@pytest.fixture
def fxt_random_video_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = f"{temp_dir}/test.mp4"

        try:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
            video_writer = cv2.VideoWriter(video_path, fourcc, 1.0, (100, 100))

            # Generate 20 random frames
            for _ in range(20):
                frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
                video_writer.write(frame)

            yield video_path
        finally:
            video_writer.release()


class TestMediaRESTEndpoint:
    def test_media_image_endpoint_post(
        self,
        fxt_resource_rest,
        fxt_random_image_file,
    ) -> None:
        # Arrange
        endpoint = f"{API_IMAGE_PATTERN}"

        # Act
        with (
            patch.object(
                MediaRESTController,
                "upload_media",
                return_value=DUMMY_DATA,
            ) as mock_upload_media,
            open(fxt_random_image_file, "rb") as f,
        ):
            result = fxt_resource_rest.post(endpoint, files={"file": ("crate.png", f, "image/png")})

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_upload_media.assert_called_once_with(
            user_id=DUMMY_USER,
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            label_info=ANY,
            media_type=IMAGE,
            file_from_request=ANY,
        )
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_image_endpoint_post_with_label(
        self,
        fxt_resource_rest,
        fxt_random_image_file,
    ) -> None:
        # Arrange
        endpoint = f"{API_IMAGE_PATTERN}"
        upload_info = '{"label_ids":["613776cec8223e455a88383d", "613776cec8223e455a88383e"]}'
        data = {"upload_info": upload_info}
        expected_upload_info = {"label_ids": ["613776cec8223e455a88383d", "613776cec8223e455a88383e"]}
        # Act
        with (
            patch.object(
                MediaRESTController,
                "upload_media",
                return_value=DUMMY_DATA,
            ) as mock_upload_media,
            open(fxt_random_image_file, "rb") as f,
        ):
            result = fxt_resource_rest.post(
                endpoint,
                files={"file": ("crate.png", f, "image/png")},
                data=data,
            )

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_upload_media.assert_called_once_with(
            user_id=DUMMY_USER,
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            label_info=expected_upload_info,
            media_type=IMAGE,
            file_from_request=ANY,
        )
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_image_endpoint_post_no_free_space(
        self,
        fxt_resource_rest,
        fxt_random_image_file,
    ) -> None:
        # Arrange
        endpoint = f"{API_IMAGE_PATTERN}"
        total_space = 1000
        free_space = 0
        used_space = total_space - free_space

        # Act and Assert
        with (
            patch.object(
                BinaryRepo,
                "get_disk_stats",
                return_value=(total_space, used_space, free_space),
            ) as mock_get_free_space,
            patch.dict(os.environ, {"FEATURE_FLAG_STORAGE_SIZE_COMPUTATION": "true"}),
            open(fxt_random_image_file, "rb") as f,
        ):
            result = fxt_resource_rest.post(endpoint, files={"file": ("crate.png", f, "image/png")})

        mock_get_free_space.assert_called_once()
        assert result.status_code == status.HTTP_507_INSUFFICIENT_STORAGE

    def test_media_video_endpoint_post(
        self,
        fxt_resource_rest,
        fxt_video_file,
    ) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}"

        # Act
        with (
            patch.object(
                MediaRESTController,
                "upload_media",
                return_value=DUMMY_DATA,
            ) as mock_upload_media,
            open(fxt_video_file, "rb") as f,
        ):
            result = fxt_resource_rest.post(endpoint, files={"file": ("test_mp4.mp4", f, "video/mp4")})

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_upload_media.assert_called_once_with(
            user_id=DUMMY_USER,
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            label_info=ANY,
            media_type=VIDEO,
            file_from_request=ANY,
        )
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_video_endpoint_post_no_free_space(
        self,
        fxt_resource_rest,
        fxt_video_file,
    ) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}"
        total_space = 1000
        free_space = 0
        used_space = total_space - free_space

        # Act and Assert
        with (
            patch.object(
                BinaryRepo,
                "get_disk_stats",
                return_value=(total_space, used_space, free_space),
            ) as mock_get_free_space,
            patch.dict(os.environ, {"FEATURE_FLAG_STORAGE_SIZE_COMPUTATION": "true"}),
            open(fxt_video_file, "rb") as f,
        ):
            result = fxt_resource_rest.post(endpoint, files={"file": ("test_mp4.mp4", f, "video/mp4")})

        assert result.status_code == status.HTTP_507_INSUFFICIENT_STORAGE
        mock_get_free_space.assert_called_once()

    def test_media_image_detail_endpoint_get(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_IMAGE_PATTERN}/{DUMMY_IMAGE_ID}"

        # Act
        with patch.object(
            MediaRESTController,
            "get_image_detail",
            return_value=DUMMY_DATA,
        ) as mock_get_detail:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_get_detail.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            image_id=DUMMY_IMAGE_ID,
        )
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_image_detail_endpoint_delete(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_IMAGE_PATTERN}/{DUMMY_IMAGE_ID}"

        # Act
        with patch.object(
            MediaRESTController,
            "delete_image",
            return_value=DUMMY_DATA,
        ) as mock_delete_image:
            result = fxt_resource_rest.delete(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_delete_image.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            image_id=DUMMY_IMAGE_ID,
        )
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_video_detail_endpoint_get(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}"

        # Act
        with patch.object(
            MediaRESTController,
            "get_video_detail",
            return_value=DUMMY_DATA,
        ) as mock_get_detail:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_get_detail.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            video_id=DUMMY_VIDEO_ID,
        )
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_media_video_detail_endpoint_delete(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}"
        # Act
        with patch.object(
            MediaRESTController,
            "delete_video",
            return_value=DUMMY_DATA,
        ) as mock_delete_video:
            result = fxt_resource_rest.delete(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_delete_video.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            video_id=DUMMY_VIDEO_ID,
        )
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    @patch(
        "communication.rest_endpoints.media_endpoints.send_file_from_path_or_url",
        return_value=DUMMY_REST_MEDIA,
    )
    def test_media_video_display_endpoint_stream(self, mock_send_file, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/display/{STREAM}"

        # Act
        with patch.object(
            MediaRESTController,
            "download_video_stream",
            return_value=DUMMY_DATA,
        ) as mock_download_video:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_send_file.assert_called_once()
        mock_download_video.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            video_id=ID(DUMMY_VIDEO_ID),
        )
        compare(result.json(), DUMMY_REST_MEDIA, ignore_eq=True)

    def test_media_video_display_endpoint_thumb(self, fxt_resource_rest, request) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/display/{THUMB}"
        # Save tmp thumbnail
        img = np.zeros([10, 10, 3], dtype=np.uint8)
        _, np_img_bytes = cv2.imencode(".jpg", img)

        # Act
        with patch.object(
            MediaRESTController,
            "get_video_thumbnail",
            return_value=io.BytesIO(bytes(np_img_bytes)),
        ) as mock_get_video_thumbnail_frame:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_get_video_thumbnail_frame.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            video_id=ID(DUMMY_VIDEO_ID),
        )

    def test_media_video_display_endpoint_thumb_stream(self, fxt_resource_rest, request) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/display/{THUMB_STREAM}"
        # Save tmp thumbnail
        image_path = tempfile.gettempdir() + "/tmp_thumbnail.jpeg"
        cv2.imwrite(image_path, np.full((10, 10, 3), 255))
        request.addfinalizer(lambda: os.remove(image_path))

        # Act
        with patch.object(
            MediaRESTController,
            "get_video_thumbnail_stream_location",
            return_value=Path(image_path),
        ) as mock_get_video_thumbnail_stream_location:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_get_video_thumbnail_stream_location.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            video_id=ID(DUMMY_VIDEO_ID),
        )

    def test_media_video_display_endpoint_unsupported(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/display/unsupported_display_type"

        # Act and Assert
        response = fxt_resource_rest.get(endpoint)
        assert response.status_code == BadRequestException.http_status

    @patch(
        "communication.rest_endpoints.media_endpoints.convert_numpy_to_jpeg_response",
        return_value=DUMMY_REST_MEDIA,
    )
    def test_media_video_frame_endpoint_full(self, mock_numpy_to_rest, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/frames/{DUMMY_FRAME_INDEX}/display/{FULL}"

        # Act
        with patch.object(
            MediaRESTController,
            "download_video_frame",
            return_value=DUMMY_DATA,
        ) as mock_download_frame:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_numpy_to_rest.assert_called_once()
        mock_download_frame.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            video_id=DUMMY_VIDEO_ID,
            frame_index=int(DUMMY_FRAME_INDEX),
        )
        compare(result.json(), DUMMY_REST_MEDIA, ignore_eq=True)

    @patch(
        "communication.rest_endpoints.media_endpoints.convert_numpy_to_jpeg_response",
        return_value=DUMMY_REST_MEDIA,
    )
    def test_media_video_frame_endpoint_thumb(self, mock_numpy_to_rest, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/frames/{DUMMY_FRAME_INDEX}/display/{THUMB}"

        # Act
        with patch.object(
            MediaRESTController,
            "download_video_frame_thumbnail",
            return_value=DUMMY_DATA,
        ) as mock_download_thumbnail:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_numpy_to_rest.assert_called_once()
        mock_download_thumbnail.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            video_id=ID(DUMMY_VIDEO_ID),
            frame_index=int(DUMMY_FRAME_INDEX),
        )
        compare(result.json(), DUMMY_REST_MEDIA, ignore_eq=True)

    def test_media_video_frame_endpoint_unsupported(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/frames/{DUMMY_FRAME_INDEX}/display/unsupported_display_type"

        # Act and Assert
        response = fxt_resource_rest.get(endpoint)
        assert response.status_code == BadRequestException.http_status

    @pytest.mark.parametrize(
        "limit, sort_by, sort_dir, expected_status",
        [
            (1, "media_name", "asc", HTTPStatus.OK),
            (2, "media_width", "dsc", HTTPStatus.OK),
            (3, "media_height", "asc", HTTPStatus.OK),
            (
                MAX_N_MEDIA_RETURNED + 1,
                "media_upload_date",
                "dsc",
                HTTPStatus.BAD_REQUEST,
            ),
        ],
    )
    def test_media_query_endpoint(self, fxt_resource_rest, limit, sort_by, sort_dir, expected_status) -> None:
        # Arrange
        endpoint = f"{API_BASE_PATTERN}/media:query?limit={limit}&sort_by={sort_by}&sort_direction={sort_dir}"
        request_data: dict = {}
        with patch.object(uuid.UUID, "hex", return_value="123456789012345678901234"):
            dataset_filter = DatasetFilter.from_dict(
                query=request_data,
                limit=min(limit, MAX_N_MEDIA_RETURNED),
                skip=0,
                sort_direction=DatasetFilterSortDirection[sort_dir.upper()],
                sort_by=DatasetFilterField[sort_by.upper()],
            )

            # Act
            with patch.object(
                MediaRESTController,
                "get_filtered_items",
                return_value=DUMMY_DATA,
            ) as mock_get_filtered_items:
                result = fxt_resource_rest.post(endpoint, json=request_data, headers=HEADERS)

            # Assert
            assert result.status_code == expected_status
            if expected_status == HTTPStatus.OK:
                mock_get_filtered_items.assert_called_once_with(
                    dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
                    dataset_filter=dataset_filter,
                )
                compare(result.json(), DUMMY_DATA, ignore_eq=True)

    @pytest.mark.parametrize(
        "limit, sort_by, sort_dir",
        [
            ("no_limit", "media_name", "asc"),
            (1, "score", "reverse"),
            (1, "label_id", "asc"),
            (1, "not_a_key", "asc"),
        ],
    )
    def test_media_query_endpoint_invalid_parameters(self, fxt_resource_rest, limit, sort_by, sort_dir) -> None:
        # Arrange
        endpoint = f"{API_BASE_PATTERN}/media:query?limit={limit}&sort_by={sort_by}&sort_direction={sort_dir}"

        # Act and Assert
        response = fxt_resource_rest.post(endpoint, json={}, headers=HEADERS)
        assert response.status_code == BadRequestException.http_status

    def test_video_query_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        limit = 10
        skip = 1
        endpoint = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}:query?limit={limit}&skip={skip}"
        # Act
        with patch.object(
            MediaRESTController,
            "get_filtered_items",
            return_value=DUMMY_DATA,
        ) as mock_get_filtered_items:
            result = fxt_resource_rest.post(endpoint, json={}, headers=HEADERS)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_get_filtered_items.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            dataset_filter=ANY,
            video_id=ID(DUMMY_VIDEO_ID),
            fps=0,
            include_frame_details=True,
        )
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    @pytest.mark.parametrize(
        "limit, sort_by, sort_dir, expected_status",
        [
            (1, "media_name", "asc", HTTPStatus.OK),
            (2, "media_width", "dsc", HTTPStatus.OK),
            (3, "media_height", "asc", HTTPStatus.OK),
            (
                MAX_N_MEDIA_RETURNED + 1,
                "media_upload_date",
                "dsc",
                HTTPStatus.BAD_REQUEST,
            ),
        ],
    )
    def test_training_revision_endpoint(
        self, fxt_resource_rest, fxt_mongo_id, limit, sort_by, sort_dir, expected_status
    ) -> None:
        # Arrange
        dataset_revision_id = fxt_mongo_id(0)
        endpoint = (
            f"{API_BASE_PATTERN}/training_revisions/{str(dataset_revision_id)}/media"
            f"?limit={limit}&sort_by={sort_by}&sort_direction={sort_dir}"
        )

        # Act
        with patch.object(
            MediaRESTController,
            "get_filtered_items",
            return_value=DUMMY_DATA,
        ) as mock_get_filtered_items:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        assert result.status_code == expected_status
        if expected_status == HTTPStatus.OK:
            mock_get_filtered_items.assert_called_once_with(
                dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
                dataset_filter=ANY,
                dataset_id=dataset_revision_id,
            )

    @pytest.mark.parametrize(
        "limit, sort_by, sort_dir",
        [
            ("no_limit", "media_name", "asc"),
            (1, "score", "reverse"),
            (1, "label_id", "asc"),
            (1, "not_a_key", "asc"),
        ],
    )
    def test_training_revision_endpoint_invalid_parameters(
        self,
        fxt_resource_rest,
        fxt_mongo_id,
        limit,
        sort_by,
        sort_dir,
    ) -> None:
        # Arrange
        dataset_revision_id = fxt_mongo_id(0)
        endpoint = (
            f"{API_BASE_PATTERN}/training_revisions/{str(dataset_revision_id)}/media"
            f"?limit={limit}&sort_by={sort_by}&sort_direction={sort_dir}"
        )

        # Act and Assert
        response = fxt_resource_rest.get(endpoint)
        assert response.status_code == BadRequestException.http_status

    @pytest.mark.parametrize(
        "limit, sort_by, sort_dir, expected_status",
        [
            (1, "media_name", "asc", HTTPStatus.OK),
            (2, "media_width", "dsc", HTTPStatus.OK),
            (3, "media_height", "asc", HTTPStatus.OK),
            (
                MAX_N_MEDIA_RETURNED + 1,
                "media_upload_date",
                "dsc",
                HTTPStatus.BAD_REQUEST,
            ),
        ],
    )
    def test_training_revision_query_endpoint(
        self, fxt_resource_rest, fxt_mongo_id, limit, sort_by, sort_dir, expected_status
    ) -> None:
        # Arrange
        dataset_revision_id = fxt_mongo_id(0)
        endpoint = (
            f"{API_BASE_PATTERN}/training_revisions/{str(dataset_revision_id)}/media"
            f":query?limit={limit}&sort_by={sort_by}&sort_direction={sort_dir}"
        )
        request_data: dict = {}
        with patch.object(uuid.UUID, "hex", return_value="123456789012345678901234"):
            dataset_filter = DatasetFilter.from_dict(
                query=request_data,
                limit=min(limit, MAX_N_MEDIA_RETURNED),
                skip=0,
                sort_direction=DatasetFilterSortDirection[sort_dir.upper()],
                sort_by=DatasetFilterField[sort_by.upper()],
            )

            # Act
            with patch.object(
                MediaRESTController,
                "get_filtered_items",
                return_value=DUMMY_DATA,
            ) as mock_get_filtered_items:
                result = fxt_resource_rest.post(endpoint, json=request_data, headers=HEADERS)

            # Assert
            assert result.status_code == expected_status
            if expected_status == HTTPStatus.OK:
                mock_get_filtered_items.assert_called_once_with(
                    dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
                    dataset_filter=dataset_filter,
                    dataset_id=dataset_revision_id,
                )
                compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_dataset_video_query_endpoint(self, fxt_resource_rest, fxt_mongo_id) -> None:
        # Arrange
        dataset_revision_id = fxt_mongo_id(0)
        limit = 10
        skip = 3
        request_data: dict = {}
        endpoint = (
            f"{API_BASE_PATTERN}/training_revisions/{str(dataset_revision_id)}"
            f"/media/videos/{DUMMY_VIDEO_ID}:query?limit={limit}&skip={skip}"
        )
        # Act
        with patch.object(
            MediaRESTController,
            "get_filtered_items",
            return_value=DUMMY_DATA,
        ) as mock_get_filtered_items:
            result = fxt_resource_rest.post(endpoint, json=request_data, headers=HEADERS)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_get_filtered_items.assert_called_once_with(
            dataset_storage_identifier=DUMMY_DATASET_STORAGE_IDENTIFIER,
            dataset_filter=ANY,
            video_id=ID(DUMMY_VIDEO_ID),
            dataset_id=dataset_revision_id,
        )
        compare(result.json(), DUMMY_DATA, ignore_eq=True)
