# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import ANY, MagicMock, patch

import pytest
from geti_types import DatasetStorageIdentifier
from iai_core.adapters.binary_interpreters import NumpyBinaryInterpreter, RAWBinaryInterpreter
from iai_core.entities.image import Image
from iai_core.entities.shapes import Polygon, Rectangle
from iai_core.entities.video import VideoFrame
from iai_core.repos.storage.binary_repos import ImageBinaryRepo, VideoBinaryRepo

from media_utils import (
    VideoFrameReader,
    get_image_bytes,
    get_image_numpy,
    get_media_numpy,
    get_media_roi_numpy,
    get_video_bytes,
    get_video_frame_numpy,
)


def return_none(*args, **kwargs) -> None:
    return None


class TestMediaUtils:
    @patch.object(ImageBinaryRepo, "__init__", new=return_none)
    def test_get_image_bytes(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        image = MagicMock()
        expected_result = MagicMock()

        # Act
        with patch.object(ImageBinaryRepo, "get_by_filename", return_value=expected_result) as patch_get_by_filename:
            result = get_image_bytes(dataset_storage_identifier=dataset_storage_identifier, image=image)

        # Assert
        assert result == expected_result
        patch_get_by_filename.assert_called_once_with(filename=image.data_binary_filename, binary_interpreter=ANY)
        assert isinstance(
            patch_get_by_filename.call_args[1]["binary_interpreter"],
            RAWBinaryInterpreter,
        )

    @patch.object(VideoBinaryRepo, "__init__", new=return_none)
    def test_get_video_bytes(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        video = MagicMock()
        expected_result = MagicMock()

        # Act
        with patch.object(VideoBinaryRepo, "get_by_filename", return_value=expected_result) as patch_get_by_filename:
            result = get_video_bytes(dataset_storage_identifier=dataset_storage_identifier, video=video)

        # Assert
        assert result == expected_result
        patch_get_by_filename.assert_called_once_with(filename=video.data_binary_filename, binary_interpreter=ANY)
        assert isinstance(
            patch_get_by_filename.call_args[1]["binary_interpreter"],
            RAWBinaryInterpreter,
        )

    @patch.object(ImageBinaryRepo, "__init__", new=return_none)
    def test_get_image_numpy(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        image = MagicMock()
        expected_result = MagicMock()

        # Act
        with patch.object(ImageBinaryRepo, "get_by_filename", return_value=expected_result) as patch_get_by_filename:
            result = get_image_numpy(dataset_storage_identifier=dataset_storage_identifier, image=image)

        # Assert
        assert result == expected_result
        patch_get_by_filename.assert_called_once_with(filename=image.data_binary_filename, binary_interpreter=ANY)
        assert isinstance(
            patch_get_by_filename.call_args[1]["binary_interpreter"],
            NumpyBinaryInterpreter,
        )

    @patch.object(VideoBinaryRepo, "__init__", new=return_none)
    def test_get_video_frame_numpy(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        video_frame = MagicMock()
        expected_result = MagicMock()

        # Act
        with patch.object(VideoFrameReader, "get_frame_numpy", return_value=expected_result) as patch_get_frame_numpy:
            result = get_video_frame_numpy(
                dataset_storage_identifier=dataset_storage_identifier,
                video_frame=video_frame,
            )

        # Assert
        assert result == expected_result
        patch_get_frame_numpy.assert_called_once_with(
            file_location_getter=ANY,
            frame_index=video_frame.frame_index,
        )
        assert callable(patch_get_frame_numpy.call_args[1]["file_location_getter"])

    def test_get_media_numpy_image(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        image = MagicMock(spec=Image)
        expected_result = MagicMock()

        # Act
        with (
            patch("media_utils.media_utils.get_image_numpy", return_value=expected_result) as patch_get_image_numpy,
            patch("media_utils.media_utils.get_video_frame_numpy") as patch_get_video_frame_numpy,
        ):
            result = get_media_numpy(dataset_storage_identifier=dataset_storage_identifier, media=image)

        # Assert
        assert result == expected_result
        patch_get_image_numpy.assert_called_once_with(
            dataset_storage_identifier=dataset_storage_identifier, image=image
        )
        patch_get_video_frame_numpy.assert_not_called()

    def test_get_media_numpy_video_frame(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        video_frame = MagicMock(spec=VideoFrame)
        expected_result = MagicMock()

        # Act
        with (
            patch("media_utils.media_utils.get_image_numpy") as patch_get_image_numpy,
            patch(
                "media_utils.media_utils.get_video_frame_numpy",
                return_value=expected_result,
            ) as patch_get_video_frame_numpy,
        ):
            result = get_media_numpy(dataset_storage_identifier=dataset_storage_identifier, media=video_frame)

        # Assert
        assert result == expected_result
        patch_get_image_numpy.assert_not_called()
        patch_get_video_frame_numpy.assert_called_once_with(
            dataset_storage_identifier=dataset_storage_identifier,
            video_frame=video_frame,
        )

    def test_get_media_roi_numpy_wrong_shape(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        media = MagicMock()
        roi_shape = MagicMock(spec=Polygon)
        expected_result = MagicMock()

        # Act
        with (
            patch("media_utils.media_utils.get_media_numpy", return_value=expected_result) as patch_get_media_numpy,
            pytest.raises(ValueError),
        ):
            get_media_roi_numpy(
                dataset_storage_identifier=dataset_storage_identifier,
                media=media,
                roi_shape=roi_shape,
            )

        # Assert
        patch_get_media_numpy.assert_not_called()

    def test_get_media_roi_numpy_none_shape(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        media = MagicMock()
        expected_result = MagicMock()

        # Act
        with patch("media_utils.media_utils.get_media_numpy", return_value=expected_result) as patch_get_media_numpy:
            result = get_media_roi_numpy(
                dataset_storage_identifier=dataset_storage_identifier,
                media=media,
                roi_shape=None,
            )

        # Assert
        assert result == expected_result
        patch_get_media_numpy.assert_called_once_with(
            dataset_storage_identifier=dataset_storage_identifier, media=media
        )

    def test_get_media_roi_numpy_one_dimensional_shape(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        media = MagicMock()
        roi_shape = MagicMock(spec=Rectangle)
        media_numpy = MagicMock()
        media_numpy.shape = [200]

        # Act
        with (
            patch("media_utils.media_utils.get_media_numpy", return_value=media_numpy) as patch_get_media_numpy,
            pytest.raises(ValueError),
        ):
            get_media_roi_numpy(
                dataset_storage_identifier=dataset_storage_identifier,
                media=media,
                roi_shape=roi_shape,
            )

        # Assert
        patch_get_media_numpy.assert_called_once_with(
            dataset_storage_identifier=dataset_storage_identifier, media=media
        )

    def test_get_media_roi_numpy(self) -> None:
        # Arrange
        dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        media = MagicMock()
        roi_shape = MagicMock(spec=Rectangle)
        media_numpy = MagicMock()
        media_numpy.shape = [200, 400]
        expected_result = MagicMock()
        roi_shape.crop_numpy_array.return_value = expected_result

        # Act
        with patch("media_utils.media_utils.get_media_numpy", return_value=media_numpy) as patch_get_media_numpy:
            result = get_media_roi_numpy(
                dataset_storage_identifier=dataset_storage_identifier,
                media=media,
                roi_shape=roi_shape,
            )

        # Assert
        assert result == expected_result
        patch_get_media_numpy.assert_called_once_with(
            dataset_storage_identifier=dataset_storage_identifier, media=media
        )
        roi_shape.crop_numpy_array.assert_called_once_with(media_numpy)
