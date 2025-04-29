# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, call, patch

import pytest

from media_utils import VideoDecoder, VideoFrameReader, VideoFrameReadingError


class TestVideoFrameReader:
    def test_get_frame_numpy_all_failures(self, request):
        # Arrange

        # Act
        with (
            patch.object(VideoDecoder, "decode", side_effect=VideoFrameReadingError) as patch_decode,
            pytest.raises(VideoFrameReadingError),
        ):
            VideoFrameReader.get_frame_numpy(
                file_location_getter=lambda: "file_location",
                frame_index=0,
            )

        # Assert
        assert patch_decode.call_count == 5
        patch_decode.assert_has_calls(
            [
                call(file_location="file_location", frame_index=0),
                call(file_location="file_location", frame_index=0),
                call(file_location="file_location", frame_index=0),
                call(file_location="file_location", frame_index=0),
                call(file_location="file_location", frame_index=0),
            ]
        )

    def test_get_frame_numpy_first_failure(self, request):
        # Arrange
        frame = MagicMock()

        # Act
        with patch.object(VideoDecoder, "decode", side_effect=[VideoFrameReadingError, frame]) as patch_decode:
            result = VideoFrameReader.get_frame_numpy(
                file_location_getter=lambda: "file_location",
                frame_index=0,
            )
        assert patch_decode.call_count == 2
        patch_decode.assert_has_calls(
            [call(file_location="file_location", frame_index=0), call(file_location="file_location", frame_index=0)]
        )
        assert result == frame

    def test_get_frame_numpy_none_frame(self, request):
        # Arrange

        # Act
        with (
            patch.object(VideoDecoder, "decode", return_value=None) as patch_decode,
            pytest.raises(VideoFrameReadingError),
        ):
            VideoFrameReader.get_frame_numpy(
                file_location_getter=lambda: "file_location",
                frame_index=0,
            )
        patch_decode.assert_called_once_with(file_location="file_location", frame_index=0)
