# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for Dataset video-related functionality.

Tests cover:
- Categorical path columns for video fields (automatic deduplication)
- VideoInfo serialization/deserialization
- Multiple videos dataset operations
- Mixed media dataset (images and video frames)
- VideoInfo stored in samples as metadata
"""

from pathlib import Path

import polars as pl

from getidata.dataset import Dataset, Sample
from getidata.fields.videos import media_path_field, video_frame_path_field, video_info_field
from getidata.media import LazyImage, LazyVideoFrame, VideoInfo

# Path to test video in assets
TEST_VIDEO_PATH = Path(__file__).parent.parent / "assets" / "cvat_dataset" / "test.mp4"


class VideoPathCategoricalTest:
    """Tests that video path columns are Categorical by default for automatic deduplication."""

    def test_video_frame_path_is_categorical(self):
        """Test that VideoFramePathField stores paths as Categorical."""

        class SimpleSample(Sample):
            frame: LazyVideoFrame = video_frame_path_field()

        dataset = Dataset(SimpleSample)

        # Add multiple samples with same video path
        for i in range(10):
            dataset.append(SimpleSample(frame=LazyVideoFrame(video_path="/path/to/video.mp4", frame_index=i)))

        # Column should be Categorical for automatic deduplication
        assert dataset.df["frame"].dtype == pl.Categorical


class VideoInfoInSampleTest:
    """Tests for storing VideoInfo as metadata directly in samples."""

    def test_sample_with_video_info_field(self):
        """Test that samples can store VideoInfo directly."""

        class VideoSample(Sample):
            frame: LazyVideoFrame = video_frame_path_field()
            video_info: VideoInfo | None = video_info_field()

        video_info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )

        dataset = Dataset(VideoSample)
        dataset.append(
            VideoSample(
                frame=LazyVideoFrame(video_path="/path/to/video.mp4", frame_index=0),
                video_info=video_info,
            )
        )

        # Retrieve sample and check video info
        sample = dataset[0]
        assert sample.video_info is not None
        assert sample.video_info.fps == 30.0
        assert sample.video_info.width == 1920
        assert sample.video_info.height == 1080
        assert sample.video_info.total_frames == 100

    def test_sample_with_media_info_field(self):
        """Test that samples can store MediaInfo (works for both images and videos)."""

        class MixedSample(Sample):
            media: LazyVideoFrame | LazyImage = media_path_field()
            media_info: VideoInfo | None = video_info_field()

        video_info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )

        dataset = Dataset(MixedSample)
        dataset.append(
            MixedSample(
                media=LazyVideoFrame(video_path="/path/to/video.mp4", frame_index=0),
                media_info=video_info,
            )
        )

        sample = dataset[0]
        assert sample.media_info is not None
        assert sample.media_info.width == 1920
        assert sample.media_info.height == 1080


class VideoInfoSerializationTest:
    """Tests for VideoInfo.to_dict() and from_dict() methods."""

    def test_video_info_to_dict(self):
        """Test VideoInfo.to_dict() serialization."""
        video_info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )

        result = video_info.to_dict()

        assert result == {
            "path": "/path/to/video.mp4",
            "total_frames": 100,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
            "duration": 3.33,
            "codec": "h264",
        }

    def test_video_info_from_dict(self):
        """Test VideoInfo.from_dict() deserialization."""
        data = {
            "path": "/path/to/video.mp4",
            "total_frames": 100,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
            "duration": 3.33,
            "codec": "h264",
        }

        video_info = VideoInfo.from_dict(data)

        assert video_info.path == "/path/to/video.mp4"
        assert video_info.total_frames == 100
        assert video_info.fps == 30.0
        assert video_info.width == 1920
        assert video_info.height == 1080
        assert video_info.duration == 3.33
        assert video_info.codec == "h264"

    def test_video_info_round_trip(self):
        """Test VideoInfo serialization round-trip."""
        original = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )

        restored = VideoInfo.from_dict(original.to_dict())

        assert restored == original

    def test_video_info_from_dict_without_codec(self):
        """Test VideoInfo.from_dict() handles missing codec gracefully."""
        data = {
            "path": "/path/to/video.mp4",
            "total_frames": 100,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
            "duration": 3.33,
        }

        video_info = VideoInfo.from_dict(data)

        assert video_info.codec is None


class MultipleVideosDatasetTest:
    """Tests for datasets containing frames from multiple video files."""

    def test_dataset_with_multiple_videos(self):
        """Test dataset with frames from multiple different videos."""

        class VideoSample(Sample):
            frame: LazyVideoFrame = video_frame_path_field()

        dataset = Dataset(VideoSample)

        # Add frames from multiple "videos"
        video1 = "/path/to/video1.mp4"
        video2 = "/path/to/video2.mp4"
        video3 = "/path/to/video3.mp4"

        for video_path in [video1, video2, video3]:
            for frame_idx in range(3):
                dataset.append(VideoSample(frame=LazyVideoFrame(video_path=video_path, frame_index=frame_idx)))

        assert len(dataset) == 9

        # Check DataFrame structure
        unique_videos = dataset.df["frame"].unique().to_list()
        assert len(unique_videos) == 3
        assert set(unique_videos) == {video1, video2, video3}

    def test_multiple_videos_with_metadata(self):
        """Test that metadata for multiple videos is stored per-sample."""

        class VideoSample(Sample):
            frame: LazyVideoFrame = video_frame_path_field()
            video_info: VideoInfo | None = video_info_field()

        dataset = Dataset(VideoSample)

        # Add samples with their own video info
        for i in range(3):
            video_path = f"/path/to/video{i}.mp4"
            video_info = VideoInfo(
                path=video_path,
                total_frames=100 + i * 50,
                fps=30.0 + i * 10,
                width=1920,
                height=1080,
                duration=3.33,
                codec="h264",
            )
            dataset.append(
                VideoSample(
                    frame=LazyVideoFrame(video_path=video_path, frame_index=0),
                    video_info=video_info,
                )
            )

        assert len(dataset) == 3

        # Verify each sample's metadata
        for i in range(3):
            sample = dataset[i]
            assert sample.video_info is not None
            assert sample.video_info.total_frames == 100 + i * 50
            assert sample.video_info.fps == 30.0 + i * 10

    def test_multiple_videos_groupby_operations(self):
        """Test groupby operations on multiple videos using Polars."""

        class VideoSample(Sample):
            frame: LazyVideoFrame = video_frame_path_field()

        dataset = Dataset(VideoSample)

        # Add frames from multiple videos with different counts
        dataset.append(VideoSample(frame=LazyVideoFrame("/video1.mp4", frame_index=0)))
        dataset.append(VideoSample(frame=LazyVideoFrame("/video1.mp4", frame_index=1)))
        dataset.append(VideoSample(frame=LazyVideoFrame("/video2.mp4", frame_index=0)))
        dataset.append(VideoSample(frame=LazyVideoFrame("/video2.mp4", frame_index=1)))
        dataset.append(VideoSample(frame=LazyVideoFrame("/video2.mp4", frame_index=2)))

        # Group by video path using Polars
        video_counts = dataset.df.group_by("frame").agg(pl.len().alias("count"))

        assert len(video_counts) == 2
        counts_dict = dict(zip(video_counts["frame"].to_list(), video_counts["count"].to_list()))
        assert counts_dict["/video1.mp4"] == 2
        assert counts_dict["/video2.mp4"] == 3


class MixedMediaDatasetTest:
    """Tests for datasets with mixed images and video frames."""

    def test_mixed_media_dataset_creation(self):
        """Test creating dataset with both images and video frames."""

        class MixedSample(Sample):
            media: LazyImage | LazyVideoFrame = media_path_field()

        dataset = Dataset(MixedSample)

        # Add image samples
        dataset.append(MixedSample(media=LazyImage("/path/to/image1.jpg")))
        dataset.append(MixedSample(media=LazyImage("/path/to/image2.jpg")))

        # Add video frame samples
        dataset.append(MixedSample(media=LazyVideoFrame("/path/to/video.mp4", frame_index=0)))
        dataset.append(MixedSample(media=LazyVideoFrame("/path/to/video.mp4", frame_index=1)))

        assert len(dataset) == 4

        # Verify DataFrame structure
        assert "media" in dataset.df.columns
        assert "media_frame_index" in dataset.df.columns

        # Check frame_index values
        frame_indices = dataset.df["media_frame_index"].to_list()
        assert frame_indices[0] is None  # Image
        assert frame_indices[1] is None  # Image
        assert frame_indices[2] == 0  # Video frame
        assert frame_indices[3] == 1  # Video frame

    def test_mixed_media_filter_by_type(self):
        """Test filtering mixed media dataset by media type using Polars."""

        class MixedSample(Sample):
            media: LazyImage | LazyVideoFrame = media_path_field()

        dataset = Dataset(MixedSample)

        # Add mixed media
        dataset.append(MixedSample(media=LazyImage("/image1.jpg")))
        dataset.append(MixedSample(media=LazyVideoFrame("/video.mp4", frame_index=0)))
        dataset.append(MixedSample(media=LazyImage("/image2.jpg")))
        dataset.append(MixedSample(media=LazyVideoFrame("/video.mp4", frame_index=1)))

        # Filter for images (frame_index is null)
        image_df = dataset.df.filter(pl.col("media_frame_index").is_null())
        assert len(image_df) == 2

        # Filter for video frames (frame_index is not null)
        video_df = dataset.df.filter(pl.col("media_frame_index").is_not_null())
        assert len(video_df) == 2

    def test_mixed_media_with_info_field(self):
        """Test mixed media dataset with MediaInfo field for both types."""

        class MixedSample(Sample):
            media: LazyImage | LazyVideoFrame = media_path_field()
            media_info: VideoInfo | None = video_info_field()

        dataset = Dataset(MixedSample)

        # Add video frame with VideoInfo
        video_info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )
        dataset.append(
            MixedSample(
                media=LazyVideoFrame("/path/to/video.mp4", frame_index=0),
                media_info=video_info,
            )
        )

        # Add image without info
        dataset.append(
            MixedSample(
                media=LazyImage("/path/to/image.jpg"),
                media_info=None,
            )
        )

        assert len(dataset) == 2

        # Video sample should have info
        video_sample = dataset[0]
        assert video_sample.media_info is not None
        assert video_sample.media_info.width == 1920

        # Image sample should not have info
        image_sample = dataset[1]
        assert image_sample.media_info is None
