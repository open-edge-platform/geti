# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests commands to map dataset items to shards"""

import pytest
from sc_sdk.entities.image import Image
from sc_sdk.entities.video import VideoFrame

from jobs_common_extras.shard_dataset.commands.map_items_to_shards_command import MapItemsToShardsCommand


@pytest.mark.JobsComponent
class TestMapItemsToShardsCommand:
    def test_image_dataset(self, fxt_dataset_with_images, fxt_subsets) -> None:
        # Arrange
        max_shard_size = 3

        # Act
        command = MapItemsToShardsCommand(
            train_dataset=fxt_dataset_with_images,
            max_shard_size=max_shard_size,
        )

        command.execute()

        # Assert
        assert {item.subset for shard in command.shards for item in shard} == set(fxt_subsets)
        # Input # of dataset items is always 10
        assert sum(len(shard) for shard in command.shards) == 10
        for shard in command.shards:
            assert len(shard) <= max_shard_size

    def test_video_dataset(self, fxt_dataset_with_video_frames, fxt_subsets) -> None:
        # Arrange
        max_shard_size = 5

        # Act
        command = MapItemsToShardsCommand(
            train_dataset=fxt_dataset_with_video_frames,
            max_shard_size=max_shard_size,
        )

        command.execute()

        # Assert
        assert {item.subset for shard in command.shards for item in shard} == set(fxt_subsets)
        # Input # of dataset items is always 10
        assert sum(len(shard) for shard in command.shards) == 10

        for shard in command.shards:
            video_ids = set()
            for item in shard:
                assert isinstance(item.media, VideoFrame)
                video_ids.add(item.media.video.id_)
            # VideoFrames should be sorted by their video id when mapping items to shards,
            # so that each shard should have at most one video in this test case
            # (5 video frames from 2 videos respectively and each shard has 5 video frames).
            assert len(video_ids) == 1

    @pytest.fixture(params=["fxt_dataset_with_images", "fxt_dataset_with_video_frames"])
    def fxt_large_media_datasets(self, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
        # Monkeypatch to mock large size media
        monkeypatch.setattr(Image, "size", 1024**3)
        monkeypatch.setattr(VideoFrame, "width", 1024**2)
        monkeypatch.setattr(VideoFrame, "height", 1024**2)

        yield request.getfixturevalue(request.param)

    def test_large_media_datasets(self, fxt_large_media_datasets):
        # Arrange
        max_shard_size = 10
        max_media_size = 1024**3

        # Act
        command = MapItemsToShardsCommand(
            train_dataset=fxt_large_media_datasets,
            max_shard_size=max_shard_size,
            max_media_size=max_media_size,
        )

        command.execute()

        # Each shard can contain at most 1 item since each media file size is heavy (1 GiB)
        assert len(command.shards) == len(fxt_large_media_datasets)
        assert all(len(shard) == 1 for shard in command.shards)
