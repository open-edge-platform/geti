# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
from entities.deployment import ModelIdentifier

from geti_types import Singleton
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


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
