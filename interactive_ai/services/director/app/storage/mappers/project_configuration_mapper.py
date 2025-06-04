# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_configuration_tools.project_configuration import ProjectConfiguration, TaskConfig

from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class TaskConfigToMongo(IMapperSimple[TaskConfig, dict]):
    """MongoDB mapper for `TaskConfig` entities"""

    @staticmethod
    def forward(instance: TaskConfig) -> dict:
        # task_id in TaskConfig is a string, but in MongoDB it is stored as an ObjectId
        doc = instance.model_dump(exclude={"task_id"})
        doc["task_id"] = IDToMongo.forward(instance.task_id)
        return doc

    @staticmethod
    def backward(instance: dict) -> TaskConfig:
        instance["task_id"] = str(IDToMongo.backward(instance["task_id"]))  # Convert ObjectId back to string
        return TaskConfig.model_validate(instance)


class ProjectConfigurationToMongo(IMapperSimple[ProjectConfiguration, dict]):
    """MongoDB mapper for `TrainingConfiguration` entities"""

    @staticmethod
    def forward(instance: ProjectConfiguration) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "task_configs": [TaskConfigToMongo.forward(task_config) for task_config in instance.task_configs],
        }

    @staticmethod
    def backward(instance: dict) -> ProjectConfiguration:
        return ProjectConfiguration(
            project_id=IDToMongo.backward(instance["_id"]),
            task_configs=[TaskConfigToMongo.backward(task_config) for task_config in instance["task_configs"]],
        )
