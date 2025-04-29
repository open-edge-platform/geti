#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for Model storage entities"""

from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo


class ModelStorageToMongo(IMapperSimple[ModelStorage, dict]):
    """MongoDB mapper for `ModelStorage` entities"""

    @staticmethod
    def forward(instance: ModelStorage) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "task_node_id": IDToMongo.forward(instance.task_node_id),
            "model_template_id": instance.model_template.model_template_id,
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
        }

    @staticmethod
    def backward(instance: dict) -> ModelStorage:
        return ModelStorage(
            id_=IDToMongo.backward(instance["_id"]),
            project_id=IDToMongo.backward(instance["project_id"]),
            task_node_id=IDToMongo.backward(instance["task_node_id"]),
            model_template=ModelTemplateList().get_by_id(instance["model_template_id"]),
            creation_date=DatetimeToMongo.backward(instance["creation_date"]),
            ephemeral=False,
        )
