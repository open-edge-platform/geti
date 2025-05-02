# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

from iai_core_py.repos.storage.binary_repos import VideoBinaryRepo

from media_utils.video_decoder import VideoDecoder
from media_utils.video_frame_reader import VideoFrameReader

logger = logging.getLogger(__name__)


class VideoFileRepair:
    """
    This class contains tools to validate, and repair some errors in video files.
    It validates videos by reading the last frame.
    If this fails, ffmpeg is ordered to re-encode the file using the same codecs and quality.
    Finally, the repair mechanism checks the file again and sees whether the repair was successful.
    """

    @staticmethod
    def _get_frame(video_binary_repo: VideoBinaryRepo, filename: str, frame_index: int) -> None:
        # Read last frame
        VideoFrameReader.get_frame_numpy(
            file_location_getter=lambda: str(video_binary_repo.get_path_or_presigned_url(filename=filename)),
            frame_index=frame_index,
        )

    @staticmethod
    def check_frame(video_binary_repo: VideoBinaryRepo, filename: str, frame_index: int) -> bool:
        """
        Checks a video by reading the last frame.

        Return whether this was successful
        :param video_binary_repo: Video binary repo
        :param filename: Video file name
        :param frame_index: Frame to try to read
        :return: boolean, whether file is valid
        """
        is_valid_video_file = False
        try:
            # Read last frame
            VideoFileRepair._get_frame(video_binary_repo=video_binary_repo, filename=filename, frame_index=frame_index)
            is_valid_video_file = True
        except Exception:
            # Ignore exception. This function will return false if the video is not valid
            logger.info("Video file is invalid and must be repaired")
        return is_valid_video_file

    @staticmethod
    def attempt_repair(video_binary_repo: VideoBinaryRepo, filename: str) -> bool:
        """
        Attempt to repair a video file. Returns a boolean indicating whether repair was successful or not.

        :param video_binary_repo: Video binary repo
        :param filename: Video file name
        :return: true/false if repair was successful
        """
        file_location = video_binary_repo.get_path_or_presigned_url(filename=filename)
        # Temp file used by ffmpeg to temporarily dump its data. Removed after use
        temporary_file_path = video_binary_repo.create_path_for_temporary_file(filename=filename, make_unique=True)
        try:
            logger.warning(f"Trying to repair video {filename}")

            import subprocess

            process = subprocess.Popen(  # noqa: S603
                [  # noqa: S607
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "warning",
                    "-y",
                    "-i",
                    file_location,
                    "-qscale:v",
                    "0",
                    "-qscale:a",
                    "0",
                    "-fps_mode:v",
                    "cfr",
                    temporary_file_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = process.communicate()
            stdout_output = stdout.decode(errors="ignore")
            stderr_output = stderr.decode(errors="ignore")
            logger.info(f"stdout of ffmpeg: {stdout_output}")
            logger.info(f"stderr of ffmpeg: {stderr_output}")
            # Give ffmpeg max 20 minutes to fix the video
            if process.wait(1200) != 0:
                return False

            # Replace the original file with the repaired file, then reset the internal state
            # of the video adapter because the cache is stale
            video_binary_repo.save(
                data_source=temporary_file_path,
                dst_file_name=filename,
                remove_source=True,
                overwrite=True,
            )
            VideoDecoder.reset_reader(file_location=str(file_location))

            # Retry reading last frame again:
            video_info = VideoDecoder.get_video_information(str(video_binary_repo.get_path_or_presigned_url(filename)))
            VideoFileRepair._get_frame(
                video_binary_repo=video_binary_repo, filename=filename, frame_index=video_info.total_frames - 1
            )
            logger.info(f"Repairing video at {filename} was successful.")

            return True
        except Exception as e:
            # We are not interested in the output. We know it has failed, so the function returns False
            logger.exception(f"Repairing video at {filename} was unsuccessful: {str(e)}")
        finally:
            if os.path.exists(temporary_file_path):
                os.unlink(temporary_file_path)
        return False

    @staticmethod
    def check_and_repair_video(video_binary_repo: VideoBinaryRepo, filename: str) -> bool:
        """
        Checks a video by reading the last frame.
        If this fails, try to repair by reconverting the video using ffmpeg.
        The quality scale is zero, making the conversion loss-less.
        Save video to original file location in binary repo.
        Then, check again if the file could be read and update the video information in the video adapter.

        :param video_binary_repo: Video binary repo
        :param filename: Video file name
        :return: True if the video file is valid, or corrected. (good for further use)
        """
        # Sanity check video
        logger.info(f"Checking video file at {filename} by reading the last frame. Repairing if needed")

        # Check the file
        video_info = VideoDecoder.get_video_information(str(video_binary_repo.get_path_or_presigned_url(filename)))
        is_valid_video_file = VideoFileRepair.check_frame(
            video_binary_repo=video_binary_repo,
            filename=filename,
            frame_index=video_info.total_frames - 1,
        )
        if is_valid_video_file:
            logger.info(f"The video file at {filename} was readable, and suitable for further use")
            result = True
        else:
            # The file was not valid
            logger.warning(f"The video file at {filename} is corrupt. Trying a repair")

            # Attempt repair
            result = VideoFileRepair.attempt_repair(video_binary_repo=video_binary_repo, filename=filename)
        return result
