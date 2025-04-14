# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Implementation of VideoFrameReader"""

import logging
import os
import time
from collections.abc import Callable

import numpy as np

from media_utils.video_decoder import VideoDecoder, VideoFrameReadingError

NUM_VIDEO_FRAME_DECODE_RETRIES = int(os.getenv("NUM_VIDEO_FRAME_DECODE_RETRIES", "5"))

logger = logging.getLogger(__name__)


class VideoFrameReader:
    @staticmethod
    def get_frame_numpy(file_location_getter: Callable[[], str], frame_index: int) -> np.ndarray:
        """
        Get frame of a video by its index

        :param file_location_getter: Function returning local storage path or presigned URL pointing to the video
        :param frame_index: Frame index (0 for first frame)
        :raises VideoFrameReadingError: if frame is not read

        :return: RGB numpy array
        """
        frame: np.ndarray | None = None
        file_location = None
        for i in range(NUM_VIDEO_FRAME_DECODE_RETRIES):
            file_location = file_location_getter()
            try:
                frame = VideoDecoder.decode(file_location=file_location, frame_index=frame_index)
                break
            except VideoFrameReadingError:
                logger.warning(
                    f"Failed attempt {i + 1}/{NUM_VIDEO_FRAME_DECODE_RETRIES} to read "
                    f"frame `{frame_index}` from video at {file_location}."
                )
                # backoff sleep times (seconds): 0.5, 1, 1.5, 2, 2.5, 3
                time.sleep(min(3.0, 0.5 * (i + 1)))

        if frame is None:
            raise VideoFrameReadingError(
                f"Unable to read frame `{frame_index}` of video file located at {file_location} "
                f"after {NUM_VIDEO_FRAME_DECODE_RETRIES} failed attempts."
            )

        return frame
