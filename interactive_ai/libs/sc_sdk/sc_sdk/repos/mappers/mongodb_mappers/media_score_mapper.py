# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

"""This module contains the MongoDB mapper for media score related entities"""

from sc_sdk.entities.media_score import MediaScore
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo
from sc_sdk.repos.mappers.mongodb_mappers.metrics_mapper import MetricToMongo


class MediaScoreToMongo(IMapperSimple[MediaScore, dict]):
    """MongoDB mapper for `MediaScore` entities"""

    @staticmethod
    def forward(instance: MediaScore) -> dict:
        doc = {
            "_id": IDToMongo.forward(instance.id_),
            "model_test_result_id": IDToMongo.forward(instance.model_test_result_id),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
            "scores": [MetricToMongo.forward(score) for score in instance.scores],
        }
        if instance.annotated_label_ids:
            doc["annotated_label_ids"] = [IDToMongo.forward(id_) for id_ in instance.annotated_label_ids]
        return doc

    @staticmethod
    def backward(instance: dict) -> MediaScore:
        annotated_label_ids = instance.get("annotated_label_ids")
        return MediaScore(
            id_=IDToMongo.backward(instance["_id"]),
            model_test_result_id=IDToMongo.backward(instance["model_test_result_id"]),
            media_identifier=MediaIdentifierToMongo.backward(instance["media_identifier"]),
            scores={MetricToMongo.backward(score) for score in instance["scores"]},  # type: ignore
            annotated_label_ids={IDToMongo.backward(id_) for id_ in annotated_label_ids}
            if annotated_label_ids
            else None,
        )
