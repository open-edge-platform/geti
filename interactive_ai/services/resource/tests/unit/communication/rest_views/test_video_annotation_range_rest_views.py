# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from testfixtures import compare

from communication.rest_views.video_annotation_range_rest_views import VideoAnnotationRangeRESTViews

from geti_types import ID
from sc_sdk.entities.video_annotation_range import RangeLabels, VideoAnnotationRange


class TestVideoAnnotationRangeRESTViews:
    def test_range_label_to_rest(self) -> None:
        range_label = RangeLabels(start_frame=3, end_frame=8, label_ids=[ID("a"), ID("b")])

        range_label_rest = VideoAnnotationRangeRESTViews.range_label_to_rest(range_label)

        assert range_label_rest == {"start_frame": 3, "end_frame": 8, "label_ids": ["a", "b"]}

    def test_range_label_from_rest(self) -> None:
        range_label_rest_1 = {"start_frame": 3, "end_frame": 8, "label_ids": ["a", "b"]}
        range_label_rest_2 = {"start_frame": 3, "end_frame": 8, "label_ids": []}

        range_label_1 = VideoAnnotationRangeRESTViews.range_label_from_rest(range_label_rest_1)
        range_label_2 = VideoAnnotationRangeRESTViews.range_label_from_rest(range_label_rest_2)

        assert range_label_1 == RangeLabels(start_frame=3, end_frame=8, label_ids=[ID("a"), ID("b")])
        assert range_label_2 is None

    def test_video_annotation_range_to_rest(self, fxt_mongo_id) -> None:
        video_ann_range = VideoAnnotationRange(
            video_id=fxt_mongo_id(1),
            range_labels=[
                RangeLabels(start_frame=0, end_frame=7, label_ids=[ID("a")]),
                RangeLabels(start_frame=8, end_frame=10, label_ids=[ID("a"), ID("b")]),
            ],
            id_=fxt_mongo_id(2),
        )

        video_ann_range_rest = VideoAnnotationRangeRESTViews.video_annotation_range_to_rest(video_ann_range)

        assert video_ann_range_rest == {
            "id": str(fxt_mongo_id(2)),
            "video_id": str(fxt_mongo_id(1)),
            "range_labels": [
                {"start_frame": 0, "end_frame": 7, "label_ids": ["a"]},
                {"start_frame": 8, "end_frame": 10, "label_ids": ["a", "b"]},
            ],
        }

    def test_video_annotation_range_from_rest(self, fxt_mongo_id) -> None:
        video_ann_range_rest = {
            "id": str(fxt_mongo_id(2)),
            "range_labels": [
                {"start_frame": 0, "end_frame": 7, "label_ids": ["a"]},
                {"start_frame": 8, "end_frame": 10, "label_ids": []},
                {"start_frame": 15, "end_frame": 20, "label_ids": ["a", "b"]},
            ],
        }

        video_ann_range = VideoAnnotationRangeRESTViews.video_annotation_range_from_rest(
            video_annotation_range_data=video_ann_range_rest,
            video_id=fxt_mongo_id(1),
        )

        assert video_ann_range == VideoAnnotationRange(
            video_id=fxt_mongo_id(1),
            range_labels=[
                RangeLabels(start_frame=0, end_frame=7, label_ids=[ID("a")]),
                RangeLabels(start_frame=15, end_frame=20, label_ids=[ID("a"), ID("b")]),
            ],
            id_=fxt_mongo_id(2),
        )

    def test_map_unmap(self, fxt_mongo_id) -> None:
        """Check if a VideoAnnotationRange can be mapped back and forth correctly."""
        range_labels = [
            RangeLabels(start_frame=0, end_frame=7, label_ids=[ID("A")]),
            RangeLabels(start_frame=8, end_frame=10, label_ids=[ID("A"), ID("B")]),
            RangeLabels(start_frame=11, end_frame=12, label_ids=[ID("A"), ID("B"), ID("C")]),
            RangeLabels(start_frame=13, end_frame=76, label_ids=[ID("B"), ID("C")]),
            RangeLabels(start_frame=77, end_frame=77, label_ids=[ID("B")]),
            RangeLabels(start_frame=95, end_frame=100, label_ids=[ID("B")]),
        ]
        video_annotation_range = VideoAnnotationRange(
            video_id=fxt_mongo_id(1),
            range_labels=range_labels,
            id_=fxt_mongo_id(2),
        )
        serialized_video_annotation_range = VideoAnnotationRangeRESTViews.video_annotation_range_to_rest(
            video_annotation_range=video_annotation_range
        )
        deserialized_video_annotation_range = VideoAnnotationRangeRESTViews.video_annotation_range_from_rest(
            video_annotation_range_data=serialized_video_annotation_range,
            video_id=video_annotation_range.video_id,
        )
        reserialized_video_annotation_range = VideoAnnotationRangeRESTViews.video_annotation_range_to_rest(
            video_annotation_range=deserialized_video_annotation_range
        )

        compare(serialized_video_annotation_range, reserialized_video_annotation_range)
        compare(video_annotation_range, deserialized_video_annotation_range)
