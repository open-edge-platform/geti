# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from iai_core.entities.project_configuration import AutoTrainingParameters, ProjectConfiguration, TaskConfig, TrainingParameters

from geti_types import ID
from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class TaskConfigToMongo(IMapperSimple[TaskConfig, dict]):
    """MongoDB mapper for `TaskConfig` entities"""

    @staticmethod
    def forward(instance: TaskConfig) -> dict:
        return {
            "task_id": IDToMongo.forward(ID(instance.task_id)),
            "training": instance.training.model_dump_json(),
            "auto_training": instance.auto_training.model_dump_json(),
        }

    @staticmethod
    def backward(instance: dict) -> TaskConfig:
        return TaskConfig(
            task_id=str(IDToMongo.backward(instance["task_id"])),
            training=TrainingParameters.model_validate_json(instance["training"]),
            auto_training=AutoTrainingParameters.model_validate_json(instance["auto_training"]),
        )


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
