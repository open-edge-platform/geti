# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the mapper to convert AutoTrainActivation to and from
a serialized representation compatible with MongoDB
"""

from entities.auto_train_activation import AutoTrainActivation

from iai_core_py.repos.mappers import DatetimeToMongo
from iai_core_py.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.mappers.mongodb_mappers.session_mapper import SessionToMongo


class AutoTrainActivationToMongo(IMapperSimple[AutoTrainActivation, dict]):
    """MongoDB mapper for `AutoTrainActivation` entities"""

    @staticmethod
    def forward(instance: AutoTrainActivation) -> dict:
        doc = {
            "_id": IDToMongo.forward(instance.id_),
            "session": SessionToMongo.forward(instance.session),
            "ready": instance.ready,
            "request_time": DatetimeToMongo.forward(instance.request_time),
        }
        if instance.model_storage_id is not None:
            doc["model_storage_id"] = IDToMongo.forward(instance.model_storage_id)
        return doc

    @staticmethod
    def backward(instance: dict) -> AutoTrainActivation:
        mongo_model_storage_id = instance.get("model_storage_id")
        model_storage_id = IDToMongo.backward(mongo_model_storage_id) if mongo_model_storage_id is not None else None
        return AutoTrainActivation(
            task_node_id=IDToMongo.backward(instance["_id"]),
            model_storage_id=model_storage_id,
            session=SessionToMongo.backward(instance["session"]),
            ready=instance.get("ready", False),
            request_time=DatetimeToMongo.backward(instance["request_time"]),
            ephemeral=False,
        )
