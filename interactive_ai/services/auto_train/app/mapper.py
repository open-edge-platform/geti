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

"""This module contains the MongoDB mapper for auto-train request entities"""

from entities import AutoTrainActivationRequest

from sc_sdk.repos.mappers import DatetimeToMongo, IDToMongo
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperBackward
from sc_sdk.repos.mappers.mongodb_mappers.session_mapper import SessionToMongo


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
