# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest
from bson import ObjectId

from sc_sdk.entities.video_annotation_range import RangeLabels, VideoAnnotationRange
from sc_sdk.repos import VideoAnnotationRangeRepo

from geti_types import ID


@pytest.mark.ScSdkComponent
class TestVideoAnnotationRangeRepo:
    def test_get_latest_by_video_id(self, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        # Arrange
        video_annotation_range_repo = VideoAnnotationRangeRepo(fxt_dataset_storage_identifier)
        video_id = fxt_ote_id(1)
        range_labels = [
            RangeLabels(start_frame=0, end_frame=7, label_ids=[ID("A")]),
            RangeLabels(start_frame=8, end_frame=10, label_ids=[ID("A"), ID("B")]),
        ]
        video_annotation_range = VideoAnnotationRange(video_id=video_id, range_labels=range_labels, id_=fxt_ote_id(2))
        with patch.object(video_annotation_range_repo, "get_one", return_value=video_annotation_range) as mock_get_one:
            # Act
            result = video_annotation_range_repo.get_latest_by_video_id(video_id=video_id)

        # Assert
        mock_get_one.assert_called_once_with(extra_filter={"video_id": ObjectId(video_id)}, latest=True)
        assert result == video_annotation_range

    def test_delete_all_by_video_id(self, fxt_dataset_storage_identifier, fxt_ote_id) -> None:
        # Arrange
        video_annotation_range_repo = VideoAnnotationRangeRepo(fxt_dataset_storage_identifier)
        video_id = fxt_ote_id(1)
        with patch.object(video_annotation_range_repo, "delete_all") as mock_delete_all:
            # Act
            video_annotation_range_repo.delete_all_by_video_id(video_id=video_id)

        # Assert
        mock_delete_all.assert_called_once_with(extra_filter={"video_id": ObjectId(video_id)})
