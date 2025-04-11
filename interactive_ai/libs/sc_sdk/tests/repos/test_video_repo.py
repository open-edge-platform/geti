# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
import os
from unittest.mock import MagicMock, patch

import pytest

from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.video import NullVideo, Video
from sc_sdk.repos import VideoRepo
from sc_sdk.repos.video_repo import VideoCache

from geti_types import DatasetStorageIdentifier, VideoFrameIdentifier


@pytest.fixture
def fxt_video_cache():
    yield VideoCache()
    VideoCache._instance = None


@pytest.mark.ScSdkComponent
class TestVideoCache:
    def test_get_or_load(self, fxt_video_cache, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        load_fn_call_count = 0

        def my_load_fn(id_):
            nonlocal load_fn_call_count
            load_fn_call_count += 1
            return video_mock

        video_mock = MagicMock(spec=Video)

        for _ in range(2):
            loaded_video = fxt_video_cache.get_or_load(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video_id=fxt_ote_id(1),
                load_fn=my_load_fn,
            )
            assert loaded_video == video_mock
            assert load_fn_call_count == 1

    def test_remove(self, fxt_video_cache, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        load_fn_call_count = 0

        def my_load_fn(id_):
            nonlocal load_fn_call_count
            load_fn_call_count += 1
            return video_mock

        video_mock = MagicMock(spec=Video)
        fxt_video_cache.get_or_load(
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            video_id=fxt_ote_id(1),
            load_fn=my_load_fn,
        )
        assert load_fn_call_count == 1

        fxt_video_cache.remove(
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            video_id=fxt_ote_id(1),
        )

        fxt_video_cache.get_or_load(
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            video_id=fxt_ote_id(1),
            load_fn=my_load_fn,
        )
        assert load_fn_call_count == 2

    def test_remove_by_dataset_storage(self, fxt_video_cache, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        load_fn_call_count = 0
        other_dataset_storage_identifier = DatasetStorageIdentifier(fxt_ote_id(51), fxt_ote_id(52), fxt_ote_id(53))

        def my_load_fn(id_):
            nonlocal load_fn_call_count
            load_fn_call_count += 1
            return video_mock

        video_mock = MagicMock(spec=Video)
        fxt_video_cache.get_or_load(
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            video_id=fxt_ote_id(1),
            load_fn=my_load_fn,
        )
        assert load_fn_call_count == 1

        fxt_video_cache.remove_all_by_dataset_storage(dataset_storage_identifier=other_dataset_storage_identifier)
        fxt_video_cache.get_or_load(
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            video_id=fxt_ote_id(1),
            load_fn=my_load_fn,
        )
        assert load_fn_call_count == 1

        fxt_video_cache.remove_all_by_dataset_storage(dataset_storage_identifier=fxt_dataset_storage_identifier)
        fxt_video_cache.get_or_load(
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            video_id=fxt_ote_id(1),
            load_fn=my_load_fn,
        )
        assert load_fn_call_count == 2


@pytest.mark.ScSdkComponent
class TestVideoRepo:
    def test_get_by_id(self, request, fxt_dataset_storage_identifier) -> None:
        video_repo = VideoRepo(fxt_dataset_storage_identifier)

        video = Video(
            name="Never gonna give you up",
            id=VideoRepo.generate_id(),
            uploader_id="",
            fps=5.0,
            width=100,
            height=50,
            total_frames=10,
            size=1000,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        request.addfinalizer(lambda: video_repo.delete_all())
        video_repo.save(video)
        with patch.object(os.path, "exists", return_value=True):
            loaded_video = video_repo.get_by_id(video.id_)

        assert loaded_video == video

    def test_get_first_video(self, request, fxt_dataset_storage_identifier) -> None:
        """
        Checks that the first video can be retrieved from the Video repo
        """

        video_repo = VideoRepo(fxt_dataset_storage_identifier)
        assert video_repo.get_one() == NullVideo()
        video_1 = Video(
            name="",
            id=VideoRepo.generate_id(),
            uploader_id="",
            fps=5.0,
            width=100,
            height=50,
            total_frames=10,
            size=1000,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        video_2 = Video(
            name="",
            id=VideoRepo.generate_id(),
            uploader_id="",
            fps=5.0,
            width=100,
            height=50,
            total_frames=10,
            size=1000,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        video_repo.save(video_1)
        video_repo.save(video_2)
        request.addfinalizer(lambda: video_repo.delete_all())

        with patch.object(os.path, "exists", return_value=True):
            assert video_repo.get_one(earliest=True) == video_1
        video_repo.delete_by_id(video_1.id_)

        with patch.object(os.path, "exists", return_value=True):
            assert video_repo.get_one(earliest=True) == video_2

    def test_delete_by_id(self, request, fxt_dataset_storage_identifier) -> None:
        video_repo = VideoRepo(fxt_dataset_storage_identifier)

        video = Video(
            name="Me at the zoo",
            id=VideoRepo.generate_id(),
            uploader_id="",
            fps=5.0,
            width=100,
            height=50,
            total_frames=10,
            size=1000,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        request.addfinalizer(lambda: video_repo.delete_all())
        video_repo.save(video)

        video_repo.delete_by_id(video.id_)

        reloaded_video = video_repo.get_by_id(video.id_)
        assert isinstance(reloaded_video, NullVideo)

    def test_delete_all(self, request, fxt_dataset_storage_identifier) -> None:
        video_repo = VideoRepo(fxt_dataset_storage_identifier)
        videos = [
            Video(
                name=f"Video #{i}",
                id=VideoRepo.generate_id(),
                uploader_id="",
                fps=5.0,
                width=100,
                height=50,
                total_frames=10,
                size=1000,
                preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
            )
            for i in range(2)
        ]
        request.addfinalizer(lambda: video_repo.delete_all())
        video_repo.save_many(videos)
        assert video_repo.count() == 2

        video_repo.delete_all()

        assert video_repo.count() == 0

    def test_get_frame_identifiers(self, request, fxt_dataset_storage_identifier) -> None:
        video_repo = VideoRepo(fxt_dataset_storage_identifier)

        videos = [
            Video(
                name=f"Video #{i}",
                id=VideoRepo.generate_id(),
                uploader_id="",
                fps=5.0,
                width=100,
                height=50,
                total_frames=10,
                size=1000,
                preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
            )
            for i in range(2)
        ]
        request.addfinalizer(lambda: video_repo.delete_all())
        video_repo.save_many(videos)

        frame_identifiers = set(video_repo.get_frame_identifiers(stride=5))

        expected_frames_1 = [VideoFrameIdentifier(videos[0].id_, i) for i in range(0, videos[0].total_frames, 5)]
        expected_frames_2 = [VideoFrameIdentifier(videos[1].id_, i) for i in range(0, videos[1].total_frames, 5)]
        assert frame_identifiers == set(expected_frames_1 + expected_frames_2)

    def test_get_all_identifiers(self, request, fxt_dataset_storage_identifier) -> None:
        video_repo = VideoRepo(fxt_dataset_storage_identifier)
        videos = [
            Video(
                name=f"Video #{i}",
                id=VideoRepo.generate_id(),
                uploader_id="",
                fps=5.0,
                width=100,
                height=50,
                total_frames=10,
                size=1000,
                preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
            )
            for i in range(3)
        ]
        request.addfinalizer(lambda: video_repo.delete_all())
        video_repo.save_many(videos)

        video_identifiers = video_repo.get_all_identifiers()

        assert set(video_identifiers) == {v.media_identifier for v in videos}

    def test_get_video_info_by_ids(self, request, fxt_dataset_storage_identifier) -> None:
        video_repo = VideoRepo(fxt_dataset_storage_identifier)
        videos = [
            Video(
                name=f"Video #{i}",
                id=VideoRepo.generate_id(),
                uploader_id="Author",
                fps=5.0,
                width=100,
                height=50,
                total_frames=10,
                size=1000,
                preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
            )
            for i in range(5)
        ]

        video_ids = [video.id_ for video in videos]
        request.addfinalizer(lambda: video_repo.delete_all())
        video_repo.save_many(videos)

        video_by_id = video_repo.get_video_by_ids(video_ids[0:5:2])

        assert len(video_by_id.keys()) == 3
        assert list(video_by_id.keys()) == video_ids[0:5:2]
