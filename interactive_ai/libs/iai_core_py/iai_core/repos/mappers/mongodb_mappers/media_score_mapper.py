# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the MongoDB mapper for media score related entities"""

from typing import Any

from iai_core.entities.media_score import MediaScore
from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo
from iai_core.repos.mappers.mongodb_mappers.metrics_mapper import MetricToMongo


class MediaScoreToMongo(IMapperSimple[MediaScore, dict]):
    """MongoDB mapper for `MediaScore` entities"""

    @staticmethod
    def forward(instance: MediaScore) -> dict:
        doc: dict[str, Any] = {
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
