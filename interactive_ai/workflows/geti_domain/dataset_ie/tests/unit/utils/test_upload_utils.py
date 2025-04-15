# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""Test import utils"""

import os.path as osp
from unittest.mock import ANY, MagicMock, patch

import datumaro as dm
import numpy as np
import pytest
from geti_telemetry_tools.metrics import (
    EmptyInstrumentAttributes,
    images_resolution_histogram,
    videos_resolution_histogram,
)
from geti_types import ID, DatasetStorageIdentifier, ImageIdentifier
from media_utils import VideoFrameOutOfRangeInternalException
from sc_sdk.entities.media import ImageExtensions
from sc_sdk.entities.video import NullVideo

from job.utils.constants import MAX_VIDEO_LENGTH, MAX_VIDEO_WIDTH, MIN_IMAGE_SIZE, MIN_VIDEO_SIZE
from job.utils.exceptions import FileNotFoundException, InvalidMediaException
from job.utils.upload_utils import AnnotationUploadManager, ImageUploadManager, VideoUploadManager


@pytest.mark.JobsComponent
class TestUploadUtils:
    @staticmethod
    def _arrange_image_uploader() -> tuple[ImageUploadManager, dm.DatasetItem]:
        uploader = ImageUploadManager(
            dataset_storage_identifier=MagicMock(), uploader_id="uploader_id", get_image_name=MagicMock()
        )
        uploader._image_repo = MagicMock()
        image_path = "/path/to/image.jpg"
        dm_item = dm.DatasetItem(id="id", media=dm.Image.from_file(image_path))
        return uploader, dm_item

    def test_image_uploader(self):
        # Arrange
        uploader, dm_item = self._arrange_image_uploader()

        # Act - normal case
        with (
            patch("job.utils.upload_utils.ConvertUtils") as convert_utils,
            patch("job.utils.upload_utils.Media2DFactory"),
            patch("job.utils.upload_utils.DatasetStorageFilterService"),
            patch("job.utils.upload_utils.publish_event"),
        ):
            convert_utils.get_image_from_dm_item.return_value = (
                np.zeros((100, 100, 3), dtype=np.float32),
                ImageExtensions.JPG,
            )
            media_info = uploader.upload(dm_item)

        # Assert
        media_info.width == MIN_IMAGE_SIZE
        media_info.height == MIN_IMAGE_SIZE
        len(uploader) == 1

        # Act - image path already exists
        media_info = uploader.upload(dm_item)

        # Assert
        media_info is None

    def test_image_uploader_cannot_convert_dm_item_to_image(self):
        # Arrange
        uploader, dm_item = self._arrange_image_uploader()

        # Act
        with pytest.raises(InvalidMediaException) as e, patch("job.utils.upload_utils.ConvertUtils") as convert_utils:
            convert_utils.get_image_from_dm_item.side_effect = ValueError("error")
            _ = uploader.upload(dm_item)

        # Assert
        assert str(e.value).startswith(f"Cannot upload image `{osp.basename(dm_item.media.path)}`.")
        assert dm_item.media.path not in str(e.value)

    def test_image_uploader_invalid_image_size(self):
        # Arrange
        uploader, dm_item = self._arrange_image_uploader()

        # Act
        with (
            pytest.raises(InvalidMediaException) as e,
            patch("job.utils.upload_utils.ConvertUtils") as convert_utils,
            patch("job.utils.upload_utils.MAX_NUMBER_OF_PIXELS", MIN_IMAGE_SIZE),
        ):
            convert_utils.get_image_from_dm_item.return_value = (
                np.zeros((MIN_IMAGE_SIZE, MIN_IMAGE_SIZE - 1, 3)),
                ImageExtensions.JPG,
            )
            _ = uploader.upload(dm_item)

        # Assert
        assert "Invalid image dimensions" in str(e.value)
        assert "The maximum number of pixels" in str(e.value)

    @staticmethod
    def _arrange_video_uploader() -> VideoUploadManager:
        uploader = VideoUploadManager(
            dataset_storage_identifier=MagicMock(), uploader_id="uploader_id", get_video_name=MagicMock()
        )
        uploader._video_repo = MagicMock()
        return uploader

    def test_video_uploader(self):
        # Arrange
        uploader = self._arrange_video_uploader()
        dm_item1 = dm.DatasetItem(id="frame", media=dm.VideoFrame(dm.Video("video1.mp4"), 1))
        dm_item2 = dm.DatasetItem(id="frame", media=dm.VideoFrame(dm.Video("video1.mp4"), 2))
        dm_item3 = dm.DatasetItem(id="frame", media=dm.VideoFrame(dm.Video("video2.mp4"), 0))

        # Act - normal case
        with (
            patch("job.utils.upload_utils.ConvertUtils") as convert_utils,
            patch("job.utils.upload_utils.VideoFrameReader"),
            patch("job.utils.upload_utils.Media2DFactory"),
            patch("job.utils.upload_utils.DatasetStorageFilterService"),
            patch("job.utils.upload_utils.publish_event"),
        ):
            convert_utils.get_video_from_dm_item.return_value = MagicMock(
                width=MIN_VIDEO_SIZE, height=MIN_VIDEO_SIZE, duration=10
            )
            video1 = uploader.upload(dm_item1)
            video2 = uploader.upload(dm_item2)
            video3 = uploader.upload(dm_item3)

        # Assert
        len(uploader) == 2
        assert not isinstance(video1, NullVideo)
        assert not isinstance(video2, NullVideo)
        assert not isinstance(video3, NullVideo)

    def test_video_uploader_null_video(self):
        # Arrange
        uploader = self._arrange_video_uploader()
        dm_item = dm.DatasetItem(id="id", media=dm.VideoFrame(dm.Video(""), 0))

        # Act
        video = uploader.upload(dm_item)

        # Assert
        assert isinstance(video, NullVideo)

    def test_video_upload_runtime_error(self):
        # Arrange
        uploader = self._arrange_video_uploader()
        video_path = "/path/to/video.mp4"
        dm_item = dm.DatasetItem(id="frame", media=dm.VideoFrame(dm.Video(video_path), 1))

        # Act
        with pytest.raises(InvalidMediaException) as e, patch("job.utils.upload_utils.ConvertUtils") as convert_utils:
            convert_utils.get_video_from_dm_item.side_effect = RuntimeError
            _ = uploader.upload(dm_item)

        # Assert
        assert str(e.value).startswith(f"Video file from `{osp.basename(video_path)}`")
        assert video_path not in str(e.value)

    def test_video_dimension_length_validation_failed(self):
        # Arrange
        uploader = self._arrange_video_uploader()
        dm_item = dm.DatasetItem(id="frame", media=dm.VideoFrame(dm.Video("video.mp4"), 1))

        # Act
        with pytest.raises(InvalidMediaException) as e, patch("job.utils.upload_utils.ConvertUtils") as convert_utils:
            convert_utils.get_video_from_dm_item.return_value = MagicMock(
                total_frames=0, width=MAX_VIDEO_WIDTH + 1, height=MIN_VIDEO_SIZE - 1, duration=MAX_VIDEO_LENGTH + 1
            )
            _ = uploader.upload(dm_item)

        # Assert
        assert "Encountered an error while decoding video" in str(e.value)
        assert "Video too small or too large" in str(e.value)
        assert "Video too long" in str(e.value)

    def test_annotations_uploader(self):
        # Arrange
        uploader = AnnotationUploadManager(
            dataset_storage_identifier=MagicMock(),
            uploader_id="uploader_id",
            project=MagicMock(),
            label_schema=MagicMock(),
            get_sc_label=MagicMock(),
        )
        uploader._ann_scene_repo = MagicMock()
        uploader._ann_scene_state_repo = MagicMock()

        dm_item = dm.DatasetItem(
            id="id",
            annotations=[
                dm.Label(0),
                dm.Bbox(1, 1, 5, 5, label=1),
                dm.Polygon((0, 0, 1, 1, 2, 2, 3, 3), label=2),
                dm.Ellipse(0, 0, 2, 2, label=3),
            ],
        )
        media_info = MagicMock()

        # Act - normal case
        with (
            patch("job.utils.upload_utils.ConvertUtils") as convert_utils,
            patch("job.utils.upload_utils.AnnotationSceneStateHelper"),
            patch("job.utils.upload_utils.publish_event"),
        ):
            convert_utils.convert_dm_anns.return_value = MagicMock()
            uploader.upload(dm_item, media_info)
            uploader.upload(dm_item, media_info)

        # Assert
        len(uploader) == 2

    @patch("job.utils.upload_utils.images_resolution_histogram")
    @patch("job.utils.upload_utils.convert_pixels")
    @patch("job.utils.upload_utils.ENABLE_METRICS", True)
    def test_update_image_metrics(self, mock_convert_pixels, mock_histogram):
        # Arrange
        image = MagicMock()
        image.width = 1920
        image.height = 1080
        mock_convert_pixels.return_value = 2073600  # Example converted pixel value
        mock_histogram.unit = images_resolution_histogram.unit

        # Act
        ImageUploadManager._update_image_metrics(image)

        # Assert
        mock_convert_pixels.assert_called_once_with(
            num_pixels=(image.width * image.height),
            unit=images_resolution_histogram.unit,
        )
        mock_histogram.record.assert_called_once_with(
            2073600,
            EmptyInstrumentAttributes().to_dict(),
        )

    @patch("job.utils.upload_utils.images_resolution_histogram")
    @patch("job.utils.upload_utils.ENABLE_METRICS", False)
    def test_update_image_metrics_metrics_disabled(self, mock_histogram):
        image = MagicMock()

        ImageUploadManager._update_image_metrics(image)

        mock_histogram.record.assert_not_called()

    @patch("job.utils.upload_utils.videos_frames_histogram")
    @patch("job.utils.upload_utils.videos_resolution_histogram")
    @patch("job.utils.upload_utils.convert_pixels")
    @patch("job.utils.upload_utils.ENABLE_METRICS", True)
    def test_update_video_metrics(self, mock_convert_pixels, mock_histogram, mock_frame_histogram):
        # Arrange
        video = MagicMock()
        video.width = 1920
        video.height = 1080
        video.total_frames = 30
        mock_convert_pixels.return_value = 2073600  # Example converted pixel value
        mock_histogram.unit = videos_resolution_histogram.unit

        # Act
        VideoUploadManager._update_video_metrics(video)

        # Assert
        mock_convert_pixels.assert_called_once_with(
            num_pixels=(video.width * video.height),
            unit=videos_resolution_histogram.unit,
        )
        mock_histogram.record.assert_called_once_with(
            2073600,
            EmptyInstrumentAttributes().to_dict(),
        )
        mock_frame_histogram.record.assert_called_once_with(
            30,
            EmptyInstrumentAttributes().to_dict(),
        )

    @patch("job.utils.upload_utils.videos_resolution_histogram")
    @patch("job.utils.upload_utils.ENABLE_METRICS", False)
    def test_update_video_metrics_metrics_disabled(self, mock_histogram):
        image = MagicMock()

        VideoUploadManager._update_video_metrics(image)

        mock_histogram.record.assert_not_called()

    @pytest.mark.parametrize(
        "side_effect, expected_error",
        [
            (FileNotFoundError, FileNotFoundException),
            (VideoFrameOutOfRangeInternalException, InvalidMediaException),
        ],
    )
    def test_video_uploader__get_video_frame_thumbnail_numpy_with_error(self, side_effect, expected_error):
        # Arrange
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=ID("workspace123"), project_id=ID("project123"), dataset_storage_id=ID("storage123")
        )
        video = MagicMock(total_frames=10)
        uploader = VideoUploadManager(dataset_storage_identifier, "uploader_id", get_video_name=MagicMock())

        with (
            patch("job.utils.upload_utils.VideoFrameReader") as video_frame_reader,
            pytest.raises(expected_error),
        ):
            video_frame_reader.get_frame_numpy.side_effect = side_effect
            uploader._get_video_frame_thumbnail_numpy(video)

    @patch("job.utils.upload_utils.publish_event")
    def test_publish_media_upload_message(self, mocked_publish_event):
        # Arrange
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=ID("workspace123"), project_id=ID("project123"), dataset_storage_id=ID("storage123")
        )
        media_identifier = ImageIdentifier(image_id=ID("image123"))

        # Act
        uploader = ImageUploadManager(dataset_storage_identifier, "uploader_id", get_image_name=MagicMock())
        uploader._publish_media_upload_message(media_identifier)

        # Assert
        expected_body = {
            "workspace_id": "workspace123",
            "project_id": "project123",
            "dataset_storage_id": "storage123",
            "media_id": "image123",
            "media_type": "image",
        }
        mocked_publish_event.assert_called_once_with(
            topic="media_uploads",
            body=expected_body,
            key=b"image123",
            headers_getter=ANY,
        )

    @patch("job.utils.upload_utils.publish_event")
    def test_publish_annotation_scene_message(self, mocked_publish_event):
        # Arrange
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=ID("workspace456"), project_id=ID("project456"), dataset_storage_id=ID("storage456")
        )
        annotation_scene_id = ID("scene789")

        # Act
        uploader = AnnotationUploadManager(
            dataset_storage_identifier=dataset_storage_identifier,
            uploader_id="uploader_id",
            project=MagicMock(),
            label_schema=MagicMock(),
            get_sc_label=MagicMock(),
        )
        uploader._publish_annotation_scene_message(annotation_scene_id)

        # Assert
        expected_body = {
            "workspace_id": "workspace456",
            "project_id": "project456",
            "dataset_storage_id": "storage456",
            "annotation_scene_id": "scene789",
        }
        mocked_publish_event.assert_called_once_with(
            topic="new_annotation_scene",
            body=expected_body,
            key=b"scene789",
            headers_getter=ANY,
        )
