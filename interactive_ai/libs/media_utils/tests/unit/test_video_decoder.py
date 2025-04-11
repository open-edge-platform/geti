# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
