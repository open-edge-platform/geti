# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the MongoDB mapper for task node related entities"""

from sc_sdk.entities.model_template import TaskFamily, TaskType
from sc_sdk.entities.task_node import TaskNode, TaskProperties
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class TaskNodeToMongo(IMapperSimple[TaskNode, dict]):
    """MongoDB mapper for `TaskNode` entities"""

    @staticmethod
    def forward(instance: TaskNode) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "title": instance.title,
            "task_type": str(instance.task_properties.task_type),
            "task_family": str(instance.task_properties.task_family),
            "is_trainable": instance.task_properties.is_trainable,
            "is_global": instance.task_properties.is_global,
            "is_anomaly": instance.task_properties.is_anomaly,
        }

    @staticmethod
    def backward(instance: dict) -> TaskNode:
        task_id = IDToMongo.backward(instance["_id"])
        task_properties = TaskProperties(
            task_type=TaskType[instance["task_type"]],
            task_family=TaskFamily[instance["task_family"]],
            is_trainable=bool(instance["is_trainable"]),
            is_global=bool(instance["is_global"]),
            is_anomaly=bool(instance["is_anomaly"]),
        )

        return TaskNode(
            id_=task_id,
            # 'project_id' is set automatically by the repo which is project-based
            project_id=IDToMongo.backward(instance["project_id"]),
            title=instance.get("title", ""),
            task_properties=task_properties,
            ephemeral=False,
        )
