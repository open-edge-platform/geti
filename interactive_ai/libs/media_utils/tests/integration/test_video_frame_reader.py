# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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

import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest
from sc_sdk.entities.shapes import Rectangle

from media_utils import VideoFrameReader
from tests.test_helpers import generate_random_annotated_project


def get_random_frame(file_location: str, total_frames: int, thread_name: str):
    n_captures = 10
    durations = []
    for _i in range(n_captures):
        try:
            rand_idx = int(np.random.random(1) * total_frames)
            start_time = time.time()
            VideoFrameReader.get_frame_numpy(file_location_getter=lambda: file_location, frame_index=rand_idx)
            duration = time.time() - start_time
            durations.append(duration)
        except BaseException:
            print(f"Fail in Thread {thread_name}!")
            raise


@pytest.mark.ScSdkComponent
class TestVideoFrameReader:
    def test_reading_video(self, request, fxt_random_annotated_video_factory) -> None:
        """
        <b>Description:</b>
        Check that a video can be read

        <b>Input data:</b>
        Randomly annotated project with a video

        <b>Expected results:</b>
        Test passes if the video can be read and a region of interest can be isolated from the frame

        <b>Steps</b>
        1. Create project with video
        2. Obtain frame from video
        3. Read two ROI
        4. Read ROI with negative index
        5. Read ROI with out of bound indices
        """
        project = generate_random_annotated_project(
            request,
            "__Test video",
            "",
            "detection",
            number_of_images=0,
            number_of_videos=0,
        )[0]
        created_video, _, _, width, height, _, file_location = fxt_random_annotated_video_factory(
            project=project, number_of_frames=10
        )

        data = VideoFrameReader.get_frame_numpy(file_location_getter=lambda: file_location, frame_index=0)

        # Try to read a ROI
        subregion = Rectangle(0, 0, 10 / width, 15 / height).crop_numpy_array(data)
        np.testing.assert_equal(data[:15, :10], subregion)

        # Try to read another ROI
        subregion = Rectangle(2 / width, 3 / height, 10 / width, 15 / height).crop_numpy_array(data)
        np.testing.assert_equal(data[3:15, 2:10], subregion)

        # Try to read a ROI with a negative index
        # The indices should be clipped to the original image dimensions
        subregion = Rectangle(-5 / width, -10 / height, 10 / width, 15 / height).crop_numpy_array(data)
        np.testing.assert_equal(data[:15, :10], subregion)

        # Try to read a ROI with out of bound indices
        # The indices should be clipped to the original image dimensions
        subregion = Rectangle(5 / width, 10 / height, (width + 10) / width, (height + 15) / height).crop_numpy_array(
            data
        )
        np.testing.assert_equal(data[10:height, 5:width], subregion)

    def test_threading_multiple_video_instances(self, request, fxt_random_annotated_video_factory) -> None:
        """
        <b>Description:</b>
        Check that video can be read on multiple threads

        <b>Input data:</b>
        Project with a video

        <b>Expected results:</b>
        Test passes if 20 threads can be used to read the video without raising an error

        <b>Steps</b>
        1. Generate project with annotated video
        2. Create 20 threads that will read a single frame
        3. Check that no errors were raised
        """
        project = generate_random_annotated_project(
            request,
            "__Test video",
            "",
            "detection",
            number_of_images=0,
            number_of_videos=0,
        )[0]
        created_video, _, fps, width, height, total_frames, file_location = fxt_random_annotated_video_factory(
            project=project, number_of_frames=10
        )

        n_threads = 5
        pool = ThreadPoolExecutor(n_threads, thread_name_prefix="test_video")
        futures = []
        for i in range(n_threads):
            futures.append(pool.submit(get_random_frame, file_location, total_frames, f"Thread-{i}"))

        # Wait for all the threads to complete.
        # This function will raise an error if any of the thread failed.
        for future in futures:
            future.result()

    def test_threading_single_video_instance(self, request, fxt_random_annotated_video_factory) -> None:
        """
        <b>Description:</b>
        Check that video can be read on multiple threads with a single video instance

        <b>Input data:</b>
        Project with a video

        <b>Expected results:</b>
        Test passes if 20 threads can be used to read the video from a single instance
        without raising an error

        <b>Steps</b>
        1. Generate project with annotated video
        2. Create 20 threads that will read one frame from a single Video instance
        3. Check that no errors were raised
        """
        project = generate_random_annotated_project(
            request,
            "__Test video",
            "",
            "detection",
            number_of_images=0,
            number_of_videos=0,
        )[0]
        created_video, _, fps, width, height, total_frames, file_location = fxt_random_annotated_video_factory(
            project=project, number_of_frames=10
        )

        n_threads = 5
        pool = ThreadPoolExecutor(n_threads, thread_name_prefix="test_video")
        futures = []
        for i in range(n_threads):
            futures.append(pool.submit(get_random_frame, file_location, total_frames, f"Thread-{i}"))

        # Wait for all the threads to complete.
        # This function will raise an error if any of the thread failed.
        for future in futures:
            future.result()
