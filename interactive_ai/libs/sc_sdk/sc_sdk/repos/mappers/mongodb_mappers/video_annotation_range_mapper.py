# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the MongoDB mapper for VideoAnnotationRanges"""

from sc_sdk.entities.video_annotation_range import RangeLabels, VideoAnnotationRange
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class RangeLabelsToMongo(IMapperSimple[RangeLabels, dict]):
    """
    This class maps a `RangeLabels` entity to a serialized dictionary that
    can be passed to MongoDB, and vice versa
    """

    @staticmethod
    def forward(instance: RangeLabels) -> dict:
        return {
            "start_frame": str(instance.start_frame),
            "end_frame": str(instance.end_frame),
            "label_ids": [IDToMongo.forward(id_) for id_ in instance.label_ids],
        }

    @staticmethod
    def backward(instance: dict) -> RangeLabels:
        return RangeLabels(
            start_frame=int(instance["start_frame"]),
            end_frame=int(instance["end_frame"]),
            label_ids=[IDToMongo.backward(id_) for id_ in instance["label_ids"]],
        )


class VideoAnnotationRangeToMongo(IMapperSimple[VideoAnnotationRange, dict]):
    """
    This class maps a `VideoAnnotationRange` entity to a serialized dictionary that
    can be passed to MongoDB, and vice versa
    """

    @staticmethod
    def forward(instance: VideoAnnotationRange) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "video_id": IDToMongo.forward(instance.video_id),
            "range_labels": [RangeLabelsToMongo().forward(range_label) for range_label in instance.range_labels],
        }

    @staticmethod
    def backward(instance: dict) -> VideoAnnotationRange:
        return VideoAnnotationRange(
            id_=IDToMongo.backward(instance["_id"]),
            video_id=IDToMongo.backward(instance["video_id"]),
            range_labels=[RangeLabelsToMongo().backward(range_label) for range_label in instance["range_labels"]],
            ephemeral=False,
        )
