# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from unittest.mock import MagicMock

import cv2
import pytest

from media_utils.video_decoder import VideoTTLCache, _clean_file_location


@pytest.fixture
def video_ttl_cache():
    return VideoTTLCache(maxsize=2, ttl=300)


class TestDecoder:
    def test_clean_file_location(self):
        presigned_url1 = "http://impt-seaweed-fs.impt:8333/videos/53e0c1c0fc131213aab78428.mp4?0987654321"
        presigned_url2 = "http://impt-seaweed-fs.impt:8333/videos/53e0c1c0fc131213aab78428.mp4?1234567890"

        cleaned_presigned_url1 = _clean_file_location(presigned_url1)
        cleaned_presigned_url2 = _clean_file_location(presigned_url2)

        assert cleaned_presigned_url1 == cleaned_presigned_url2

    @pytest.mark.parametrize("mock_release", [MagicMock(spec=cv2.VideoCapture)])
    def test_release_opencv_video_capture_on_removal(self, mock_release, video_ttl_cache):
        video_ttl_cache["video1"] = (mock_release, None)
        del video_ttl_cache["video1"]
        mock_release.release.assert_called_once()
