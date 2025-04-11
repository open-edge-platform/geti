# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""
This module implements the mapper to convert AutoTrainActivation to and from
a serialized representation compatible with MongoDB
"""

from entities.auto_train_activation import AutoTrainActivation

from sc_sdk.repos.mappers import DatetimeToMongo
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.session_mapper import SessionToMongo


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
