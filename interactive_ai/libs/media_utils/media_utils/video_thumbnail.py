# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
import subprocess
import tempfile

logger = logging.getLogger(__name__)


def generate_thumbnail_video(
    data_binary_url: str,
    thumbnail_video_path: str,
    video_width: int,
    video_height: int,
    default_thumbnail_size: int,
) -> None:
    """
    Generates a video thumbnail and saves it to a local FS to temporary file.
    Tries to maintain aspect ratio up until 16:9 when generating the thumbnail video.
    Anything above that will be squared.

    :param data_binary_url: Video binary file URL
    :param thumbnail_video_path: Path to write generated thumbnail video to
    :param video_width: Video width
    :param video_height: Video height
    :param default_thumbnail_size: Default thumbnail size
    :return str: generated thumbnail video file path
    """
    aspect_ratio = video_width / video_height
    target_resolution = f"{default_thumbnail_size}:{default_thumbnail_size}"
    if 1 < aspect_ratio < 1.8:
        target_resolution = f"{default_thumbnail_size}:-2"

    _, tmp_thumbnail_path = tempfile.mkstemp()
    process = subprocess.Popen(  # noqa: S603
        [  # noqa: S607
            "ffmpeg",
            "-threads",
            "1",
            "-y",
            "-i",
            data_binary_url,
            "-vf",
            f"scale={target_resolution}",
            "-r",
            "1",
            "-an",
            "-threads",
            "1",
            thumbnail_video_path,
        ],
    )
    # Since this method is usually called from a Kafka event, this needs to complete within 15 minutes so the
    # Kafka consumer is not kicked out for exceeding the polling interval.
    exit_code = process.wait(timeout=885)
    if exit_code != 0:
        logger.warning(f"Failed writing thumbnail video for video {data_binary_url} with exit code: {exit_code}")
