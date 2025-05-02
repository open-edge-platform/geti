# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the MongoDB mapper for CodeDeployment entities"""

from entities.deployment import CodeDeployment, DeploymentState
from repos.model_identifier_mapper import ModelIdentifierToMongo

from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo


class CodeDeploymentToMongo(IMapperSimple[CodeDeployment, dict]):
    """MongoDB mapper for `CodeDeployment` entities"""

    @staticmethod
    def forward(instance: CodeDeployment) -> dict:
        return {
            "creator_id": str(instance.creator_id),
            "_id": IDToMongo.forward(instance.id_),
            "progress": float(instance.progress),
            "state": instance.state.name,
            "message": instance.message,
            "model_identifiers": [
                ModelIdentifierToMongo().forward(model_identifier) for model_identifier in instance.model_identifiers
            ],
            "binary_filename": instance.binary_filename,
            "creation_time": DatetimeToMongo.forward(instance.creation_time),
        }

    @staticmethod
    def backward(instance: dict) -> CodeDeployment:
        creation_time = DatetimeToMongo.backward(instance.get("creation_time"))

        return CodeDeployment(
            id_=IDToMongo.backward(instance["_id"]),
            creator_id=str(instance["creator_id"]),
            progress=instance["progress"],
            state=DeploymentState[instance["state"]],
            message=instance["message"],
            model_identifiers=[
                ModelIdentifierToMongo().backward(model_identifier)
                for model_identifier in instance["model_identifiers"]
            ],
            binary_filename=instance["binary_filename"],
            ephemeral=False,
            creation_time=creation_time,
        )
