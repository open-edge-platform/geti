# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import copy

import pytest
from testfixtures import compare

from iai_core_py.entities.video_annotation_range import RangeLabels, VideoAnnotationRange

from geti_types import ID

non_normalized_range_labels = [
    RangeLabels(start_frame=0, end_frame=10, label_ids=[ID("A")]),
    RangeLabels(start_frame=8, end_frame=77, label_ids=[ID("B")]),
    RangeLabels(start_frame=10, end_frame=12, label_ids=[ID("A")]),
    RangeLabels(start_frame=11, end_frame=76, label_ids=[ID("C")]),
    RangeLabels(start_frame=95, end_frame=100, label_ids=[ID("B")]),
]

normalized_range_labels = [
    RangeLabels(start_frame=0, end_frame=7, label_ids=[ID("A")]),
    RangeLabels(start_frame=8, end_frame=10, label_ids=[ID("A"), ID("B")]),
    RangeLabels(start_frame=11, end_frame=12, label_ids=[ID("A"), ID("B"), ID("C")]),
    RangeLabels(start_frame=13, end_frame=76, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=77, end_frame=77, label_ids=[ID("B")]),
    RangeLabels(start_frame=95, end_frame=100, label_ids=[ID("B")]),
]


inserted_normalized_range_labels_1 = [
    RangeLabels(start_frame=13, end_frame=76, label_ids=[ID("B"), ID("C")]),
]


inserted_normalized_range_labels_2 = [
    RangeLabels(start_frame=13, end_frame=41, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=42, end_frame=42, label_ids=[ID("A")]),
    RangeLabels(start_frame=43, end_frame=76, label_ids=[ID("B"), ID("C")]),
]

inserted_normalized_range_labels_3 = [
    RangeLabels(start_frame=0, end_frame=0, label_ids=[ID("A")]),
    RangeLabels(start_frame=13, end_frame=41, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=42, end_frame=42, label_ids=[ID("A")]),
    RangeLabels(start_frame=43, end_frame=76, label_ids=[ID("B"), ID("C")]),
]

inserted_normalized_range_labels_4 = [
    RangeLabels(start_frame=0, end_frame=0, label_ids=[ID("A")]),
    RangeLabels(start_frame=13, end_frame=41, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=42, end_frame=42, label_ids=[ID("A")]),
    RangeLabels(start_frame=43, end_frame=75, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=76, end_frame=76, label_ids=[ID("A")]),
]

inserted_normalized_range_labels_5 = [
    RangeLabels(start_frame=0, end_frame=0, label_ids=[ID("A")]),
    RangeLabels(start_frame=13, end_frame=41, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=42, end_frame=42, label_ids=[ID("A")]),
    RangeLabels(start_frame=43, end_frame=75, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=76, end_frame=76, label_ids=[ID("B")]),
]

inserted_normalized_range_labels_6 = [
    RangeLabels(start_frame=0, end_frame=0, label_ids=[ID("A")]),
    RangeLabels(start_frame=13, end_frame=41, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=42, end_frame=42, label_ids=[ID("A")]),
    RangeLabels(start_frame=43, end_frame=49, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=51, end_frame=75, label_ids=[ID("B"), ID("C")]),
    RangeLabels(start_frame=76, end_frame=76, label_ids=[ID("B")]),
]


class TestRangeLabels:
    def test_invalid_range_labels(self) -> None:
        """
        Tests if invalid RangeLabels raise an error
        """
        with pytest.raises(ValueError):
            RangeLabels(start_frame=50, end_frame=43, label_ids=[ID("A")])
        with pytest.raises(ValueError):
            RangeLabels(start_frame=-1, end_frame=43, label_ids=[ID("A")])
        with pytest.raises(ValueError):
            RangeLabels(start_frame=0, end_frame=43, label_ids=[])


class TestVideoAnnotationRange:
    def test_normalization_on_init(self, fxt_mongo_id) -> None:
        """
        Tests if the VideoAnnotationRange class properly normalizes the range labels.
        """
        non_normalized_range_labels_copy = copy.deepcopy(non_normalized_range_labels)
        video_annotation_range = VideoAnnotationRange(
            video_id=fxt_mongo_id,
            range_labels=non_normalized_range_labels,
            id_=fxt_mongo_id(2),
        )
        for range_label, normalized_range_label in zip(
            video_annotation_range.range_labels, normalized_range_labels, strict=True
        ):
            assert range_label.start_frame == normalized_range_label.start_frame
            assert range_label.end_frame == normalized_range_label.end_frame
            assert sorted(range_label.label_ids) == sorted(normalized_range_label.label_ids)
        assert non_normalized_range_labels_copy == non_normalized_range_labels

    def test_get_labels_at_frame_index(self, fxt_mongo_id) -> None:
        range_labels = [
            RangeLabels(start_frame=1, end_frame=4, label_ids=[ID("A")]),
            RangeLabels(start_frame=7, end_frame=7, label_ids=[ID("B")]),
            RangeLabels(start_frame=8, end_frame=10, label_ids=[ID("C")]),
        ]
        video_annotation_range = VideoAnnotationRange(
            video_id=fxt_mongo_id,
            range_labels=range_labels,
            id_=fxt_mongo_id(2),
        )
        expected_labels_by_frame: tuple[tuple[int, set[ID]], ...] = (
            (0, set()),
            (1, {ID("A")}),
            (2, {ID("A")}),
            (4, {ID("A")}),
            (5, set()),
            (7, {ID("B")}),
            (8, {ID("C")}),
            (11, set()),
        )

        for frame_index, expected_labels in expected_labels_by_frame:
            found_labels = video_annotation_range.get_labels_at_frame_index(frame_index=frame_index)
            assert found_labels == expected_labels, (
                f"Wrong label for frame index {frame_index}: expected {expected_labels}, got {found_labels}"
            )

    def test_set_labels_at_frame_index(self, fxt_mongo_id) -> None:
        """
        Tests inserting single frame labels into an existing video range object.
        """
        # Create object with one existing range
        video_annotation_range = VideoAnnotationRange(
            video_id=fxt_mongo_id(1),
            range_labels=inserted_normalized_range_labels_1,
            id_=fxt_mongo_id(2),
        )
        # Insert a new frame within the existing range
        video_annotation_range.set_labels_at_frame_index(frame_index=42, label_ids=[ID("A")])
        compare(video_annotation_range.range_labels, inserted_normalized_range_labels_2)

        # Insert a new frame at the beginning of the range
        video_annotation_range.set_labels_at_frame_index(frame_index=0, label_ids=[ID("A")])
        compare(video_annotation_range.range_labels, inserted_normalized_range_labels_3)

        # Insert a new frame at the end of the range
        video_annotation_range.set_labels_at_frame_index(frame_index=76, label_ids=[ID("A")])
        compare(video_annotation_range.range_labels, inserted_normalized_range_labels_4)

        # Overwrite a label within an existing range
        video_annotation_range.set_labels_at_frame_index(frame_index=76, label_ids=[ID("B")])
        compare(video_annotation_range.range_labels, inserted_normalized_range_labels_5)

        # Remove all labels from a frame that is NOT part of an existing range
        video_annotation_range.set_labels_at_frame_index(frame_index=8, label_ids=[])
        compare(video_annotation_range.range_labels, inserted_normalized_range_labels_5)

        # Remove all labels from a frame that is part of an existing range
        video_annotation_range.set_labels_at_frame_index(frame_index=50, label_ids=[])
        compare(video_annotation_range.range_labels, inserted_normalized_range_labels_6)
