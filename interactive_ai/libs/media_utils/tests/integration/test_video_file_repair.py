# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

from sc_sdk.repos.storage.binary_repos import VideoBinaryRepo

from media_utils import VideoDecoder, VideoFileRepair


class TestVideoRepair:
    def test_valid(self, request, fxt_dataset_storage_identifier, fxt_repaired_video):
        """
        <b>Description:</b>
        Check that a valid video file is not repaired.

        <b>Input data:</b>
        A valid video file.

        <b>Expected results:</b>
        It should evaluate the file as a valid file and not repair it.

        <b>Steps</b>
        1. Save a valid video file and store the binary filename in the video adapter
        2. Check that the check_video and check_and_repair_video methods both evaluate the video as being valid
        3. Assert that no repair action was started
        """
        video_binary_repo = VideoBinaryRepo(fxt_dataset_storage_identifier)
        valid_video_filename = video_binary_repo.save(
            dst_file_name=str(fxt_repaired_video), data_source=str(fxt_repaired_video)
        )
        request.addfinalizer(lambda: video_binary_repo.delete_by_filename(filename=valid_video_filename))
        video_info = VideoDecoder.get_video_information(str(fxt_repaired_video))

        with patch.object(VideoFileRepair, "attempt_repair", return_value=None) as patch_repair:
            is_valid_check = VideoFileRepair.check_frame(
                video_binary_repo=video_binary_repo,
                filename=valid_video_filename,
                frame_index=video_info.total_frames - 1,
            )
            is_valid_check_and_repair = VideoFileRepair.check_and_repair_video(
                video_binary_repo=video_binary_repo, filename=valid_video_filename
            )

            assert is_valid_check
            assert is_valid_check_and_repair
            patch_repair.assert_not_called()

    def test_repairable(self, request, fxt_dataset_storage_identifier, fxt_repairable_video):
        """
        <b>Description:</b>
        Check that a repairable video file is sent to get repaired.

        <b>Input data:</b>
        A repairable video file.

        <b>Expected results:</b>
        It should evaluate the file as an invalid file and proceed to repair it.

        <b>Steps</b>
        1. Save a repairable video file and store its filename in the video adapter
        2. Check that the repairable video file is not readable.
        3. Check that the repairable video file is repaired after calling check_and_repair.
        """
        video_binary_repo = VideoBinaryRepo(fxt_dataset_storage_identifier)
        repairable_video_filename = video_binary_repo.save(
            dst_file_name=str(fxt_repairable_video), data_source=str(fxt_repairable_video)
        )
        request.addfinalizer(lambda: video_binary_repo.delete_by_filename(filename=repairable_video_filename))
        video_info = VideoDecoder.get_video_information(str(fxt_repairable_video))

        is_valid = VideoFileRepair.check_frame(
            video_binary_repo=video_binary_repo,
            filename=repairable_video_filename,
            frame_index=video_info.total_frames - 1,
        )
        assert not is_valid, "Expected to have the repairable video file to be invalid after check"
        is_valid = VideoFileRepair.check_and_repair_video(
            video_binary_repo=video_binary_repo,
            filename=repairable_video_filename,
        )
        assert is_valid, "Expected to have the repairable video file to be valid after check and repair"

    def test_unrepairable(self, request, fxt_dataset_storage_identifier, fxt_unrepairable_video):
        """
        <b>Description:</b>
        Check that an unrepairable video file cannot be repaired.

        <b>Input data:</b>
        An unrepairable video file (it's not a video, it's a random file zip renamed to mp4).

        <b>Expected results:</b>
        It should not evaluate it as valid, and not be able to repair it.

        <b>Steps</b>
        1. Save an unrepairable video file and store its filename in the video adapter
        2. Check that the video file is not readable.
        3. Check that the video is not valid after repair as it is not repairable
        """
        video_binary_repo = VideoBinaryRepo(fxt_dataset_storage_identifier)
        unrepairable_video_filename = video_binary_repo.save(
            dst_file_name=str(fxt_unrepairable_video), data_source=str(fxt_unrepairable_video)
        )
        request.addfinalizer(lambda: video_binary_repo.delete_by_filename(unrepairable_video_filename))
        video_info = VideoDecoder.get_video_information(str(fxt_unrepairable_video))

        is_valid = VideoFileRepair.check_frame(
            video_binary_repo=video_binary_repo,
            filename=unrepairable_video_filename,
            frame_index=video_info.total_frames - 1,
        )
        assert not is_valid, "Expected to have the unrepairable video file to be invalid after check"
        is_valid = VideoFileRepair.check_and_repair_video(
            video_binary_repo=video_binary_repo,
            filename=unrepairable_video_filename,
        )
        assert not is_valid, "Expected to have the repairable video file to be valid after check and repair"
