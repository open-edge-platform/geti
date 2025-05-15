# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from entities.deployment import ModelIdentifier

from geti_types import Singleton
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class ModelIdentifierToMongo(metaclass=Singleton):
    """
    This class maps a `ModelIdentifier` entity to a serialized dictionary that
    can be passed to MongoDB, and vice versa
    """

    @staticmethod
    def forward(
        instance: ModelIdentifier,
    ) -> dict:
        return {
            "model_id": IDToMongo.forward(instance.model_id),
            "model_storage_id": IDToMongo.forward(instance.model_storage_id),
        }

    @staticmethod
    def backward(
        instance: dict,
    ) -> ModelIdentifier:
        return ModelIdentifier(
            model_id=IDToMongo.backward(instance["model_id"]),
            model_storage_id=IDToMongo.backward(instance["model_storage_id"]),
        )
