# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the MongoDB mappers for active score entities"""

from active_learning.entities import ActiveScore, TaskActiveScore

from geti_types import ID
from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple

__all__ = ["ActiveScoreToMongo"]

from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo


class TaskActiveScoreToMongo(IMapperSimple[TaskActiveScore, dict]):
    """MongoDB mapper for `TaskActiveScore` entities"""

    @staticmethod
    def forward(instance: TaskActiveScore) -> dict:
        model_id = IDToMongo.forward(instance.model_id) if instance.model_id is not None else None
        return {
            "score": instance.score,
            "model_id": model_id,
            "extractors_scores": [
                {
                    "name": extr_name,
                    "score": extr_score,
                }
                for extr_name, extr_score in instance.extractors_scores.items()
            ],
        }

    @staticmethod
    def backward(instance: dict) -> TaskActiveScore:
        model_id = instance.get("model_id")
        model_id = ID() if model_id is None else IDToMongo.backward(model_id)
        extractors_scores = {
            extr_dict["name"]: extr_dict["score"] for extr_dict in instance.get("extractors_scores", [])
        }
        return TaskActiveScore(
            score=instance.get("score", 1.0),
            model_id=model_id,
            extractors_scores=extractors_scores,
        )


class ActiveScoreToMongo(IMapperSimple[ActiveScore, dict]):
    """MongoDB mapper for `ActiveScore` entities"""

    @staticmethod
    def forward(instance: ActiveScore) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
            "score": instance.pipeline_score,
            "tasks": [
                dict(
                    TaskActiveScoreToMongo.forward(task_score),
                    task_node_id=IDToMongo.forward(task_node_id),
                )
                for task_node_id, task_score in instance.tasks_scores.items()
            ],
        }

    @staticmethod
    def backward(instance: dict) -> ActiveScore:
        media_identifier = MediaIdentifierToMongo.backward(instance["media_identifier"])
        pipeline_score = instance["score"]
        tasks_scores = {
            IDToMongo.backward(task_score_dict["task_node_id"]): TaskActiveScoreToMongo.backward(task_score_dict)
            for task_score_dict in instance["tasks"]
        }
        return ActiveScore(
            media_identifier=media_identifier,
            pipeline_score=pipeline_score,
            tasks_scores=tasks_scores,
            ephemeral=False,
        )
