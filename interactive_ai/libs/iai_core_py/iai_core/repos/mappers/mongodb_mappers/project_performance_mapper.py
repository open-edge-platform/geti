#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for project performance entities"""

from typing import Any

from iai_core.entities.project_performance import (
    GlobalLocalTaskPerformance,
    ProjectPerformance,
    TaskPerformance,
    TaskPerformanceScore,
)
from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class TaskPerformanceScoreToMongo(IMapperSimple[TaskPerformanceScore, dict]):
    """mongoDB mapper for `TaskPerformanceScore` entities"""

    @staticmethod
    def forward(instance: TaskPerformanceScore) -> dict:
        return {
            "value": instance.value,
            "metric_type": instance.metric_type,
        }

    @staticmethod
    def backward(instance: dict) -> TaskPerformanceScore:
        return TaskPerformanceScore(
            value=instance["value"],
            metric_type=instance["metric_type"],
        )


class TaskPerformanceToMongo(IMapperSimple[TaskPerformance, dict]):
    """MongoDB mapper for `TaskPerformance` entities"""

    @staticmethod
    def forward(instance: TaskPerformance) -> dict:
        result_dict: dict[str, Any] = {"task_node_id": IDToMongo.forward(instance.task_node_id)}

        score_dict: dict | None = None
        if instance.score is not None:
            score_dict = TaskPerformanceScoreToMongo.forward(instance.score)

        result_dict["score"] = score_dict

        if isinstance(instance, GlobalLocalTaskPerformance):
            global_score_dict = TaskPerformanceScoreToMongo.forward(instance.global_score)  # type: ignore
            local_score_dict: dict | None = None
            if instance.local_score is not None:
                local_score_dict = TaskPerformanceScoreToMongo.forward(instance.local_score)

            result_dict["global_score"] = global_score_dict
            result_dict["local_score"] = local_score_dict

        return result_dict

    @staticmethod
    def backward(instance: dict) -> TaskPerformance:
        task_node_id = IDToMongo.backward(instance["task_node_id"])
        score_dict = instance["score"]
        global_score_dict = instance.get("global_score")
        local_score_dict = instance.get("local_score")

        task_performance: TaskPerformance
        if global_score_dict is not None:
            global_score = TaskPerformanceScoreToMongo.backward(global_score_dict)
            local_score: TaskPerformanceScore | None = None
            if local_score_dict is not None:
                local_score = TaskPerformanceScoreToMongo.backward(local_score_dict)

            task_performance = GlobalLocalTaskPerformance(
                task_node_id=task_node_id,
                global_score=global_score,
                local_score=local_score,
            )
        else:
            score: TaskPerformanceScore | None = None
            if score_dict is not None:
                score = TaskPerformanceScoreToMongo.backward(score_dict)

            task_performance = TaskPerformance(task_node_id=task_node_id, score=score)

        return task_performance


class ProjectPerformanceToMongo(IMapperSimple[ProjectPerformance, dict]):
    """MongoDB mapper for `ProjectPerformance` entities"""

    @staticmethod
    def forward(instance: ProjectPerformance) -> dict:
        return {
            "score": instance.score,
            "task_performances": [
                TaskPerformanceToMongo.forward(task_performance)
                for task_performance in instance.task_performances.values()
            ],
        }

    @staticmethod
    def backward(instance: dict) -> ProjectPerformance:
        score = instance["score"]
        task_performances = [
            TaskPerformanceToMongo.backward(task_performance_dict)
            for task_performance_dict in instance["task_performances"]
        ]
        return ProjectPerformance(score=score, task_performances=task_performances)
