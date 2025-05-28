# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_configuration_tools.training_configuration import PartialTrainingConfiguration

from geti_types import ID
from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class PartialTrainingConfigurationToMongo(IMapperSimple[PartialTrainingConfiguration, dict]):
    """MongoDB mapper for `TrainingConfiguration` entities"""

    @staticmethod
    def forward(instance: PartialTrainingConfiguration) -> dict:
        doc = {
            "_id": IDToMongo.forward(instance.id_),
            "task_id": IDToMongo.forward(ID(instance.task_id)),
            "global_parameters": instance.global_parameters.model_dump(),
            "hyperparameters": instance.hyperparameters.model_dump(),
        }
        if instance.model_manifest_id:
            doc["model_manifest_id"] = instance.model_manifest_id
        return doc

    @staticmethod
    def backward(instance: dict) -> PartialTrainingConfiguration:
        partial_model_dict = {
            "id_": IDToMongo.backward(instance["_id"]),
            "task_id": IDToMongo.backward(instance["task_id"]),
            "model_manifest_id": instance.get("model_manifest_id"),
            "global_parameters": instance.get("global_parameters"),
            "hyperparameters": instance.get("hyperparameters"),
        }
        return PartialTrainingConfiguration.model_validate(partial_model_dict)
