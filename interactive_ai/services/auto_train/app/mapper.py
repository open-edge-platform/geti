# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the MongoDB mapper for auto-train request entities"""

from entities import AutoTrainActivationRequest

from iai_core.repos.mappers import DatetimeToMongo, IDToMongo
from iai_core.repos.mappers.mongodb_mapper_interface import IMapperBackward
from iai_core.repos.mappers.mongodb_mappers.session_mapper import SessionToMongo


class AutoTrainActivationToMongo(IMapperBackward[AutoTrainActivationRequest, dict]):
    """MongoDB mapper for `AutoTrainActivationRequest` entities"""

    @staticmethod
    def backward(instance: dict) -> AutoTrainActivationRequest:
        mongo_model_storage_id = instance.get("model_storage_id")
        model_storage_id = IDToMongo.backward(mongo_model_storage_id) if mongo_model_storage_id is not None else None
        return AutoTrainActivationRequest(
            project_id=IDToMongo.backward(instance["project_id"]),
            task_node_id=IDToMongo.backward(instance["_id"]),
            model_storage_id=model_storage_id,
            session=SessionToMongo.backward(instance["session"]),
            ready=instance.get("ready", False),
            bypass_debouncer=instance.get("bypass_debouncer", False),
            timestamp=DatetimeToMongo.backward(instance["request_time"]),
            ephemeral=False,
        )
