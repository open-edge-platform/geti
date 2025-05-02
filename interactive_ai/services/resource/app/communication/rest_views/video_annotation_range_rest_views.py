# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Any

from communication.rest_views.annotation_rest_views import ID_

from geti_telemetry_tools import unified_tracing
from geti_types import ID
from iai_core.entities.video_annotation_range import RangeLabels, VideoAnnotationRange
from iai_core.repos import VideoAnnotationRangeRepo

START_FRAME = "start_frame"
END_FRAME = "end_frame"
VIDEO_ID = "video_id"
LABEL_IDS = "label_ids"
RANGE_LABELS = "range_labels"


class VideoAnnotationRangeRESTViews:
    """
    This class maps VideoAnnotationRange entities to a REST View (and vice versa)
    """

    @staticmethod
    def range_label_to_rest(range_label: RangeLabels) -> dict:
        """
        Maps a RangeLabels entity to a REST View

        :param range_label: RangeLabels entity
        :return: REST View
        """
        return {
            START_FRAME: range_label.start_frame,
            END_FRAME: range_label.end_frame,
            LABEL_IDS: [str(label_id) for label_id in range_label.label_ids],
        }

    @staticmethod
    def range_label_from_rest(range_label: dict) -> RangeLabels | None:
        """
        Initialize a RangeLabels entity from its equivalent REST representation

        :param range_label: RangeLabels dict
        :return: RangeLabels object, or None if the list of labels is empty
        """
        if not range_label[LABEL_IDS]:
            return None
        return RangeLabels(
            start_frame=int(range_label[START_FRAME]),
            end_frame=int(range_label[END_FRAME]),
            label_ids=[ID(label_id) for label_id in range_label[LABEL_IDS]],
        )

    @staticmethod
    @unified_tracing
    def video_annotation_range_to_rest(
        video_annotation_range: VideoAnnotationRange,
    ) -> dict[str, Any]:
        """
        Maps a VideoAnnotationRange entity to a REST View

        :param video_annotation_range: VideoAnnotationRange entity
        :return: REST View
        """
        return {
            ID_: str(video_annotation_range.id_),
            VIDEO_ID: str(video_annotation_range.video_id),
            RANGE_LABELS: [
                VideoAnnotationRangeRESTViews.range_label_to_rest(range_label)
                for range_label in video_annotation_range.range_labels
            ],
        }

    @staticmethod
    @unified_tracing
    def video_annotation_range_from_rest(video_annotation_range_data: dict, video_id: ID) -> VideoAnnotationRange:
        """
        Maps a VideoAnnotationRange entity from a REST View

        :param video_annotation_range_data: VideoAnnotationRange dict
        :param video_id: ID of the video
        :return: VideoAnnotationRange
        """
        id_ = video_annotation_range_data.get(ID_, VideoAnnotationRangeRepo.generate_id())
        range_labels: list[RangeLabels] = []
        for range_label_data in video_annotation_range_data[RANGE_LABELS]:
            range_label = VideoAnnotationRangeRESTViews.range_label_from_rest(range_label_data)
            if range_label is not None:
                range_labels.append(range_label)
        return VideoAnnotationRange(id_=id_, video_id=video_id, range_labels=range_labels)
