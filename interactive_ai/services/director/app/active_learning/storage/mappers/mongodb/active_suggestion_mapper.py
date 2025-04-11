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

"""This module implements the MongoDB mappers for active suggestion entities"""

from active_learning.entities import ActiveSuggestion

from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple

__all__ = ["ActiveSuggestionToMongo"]

from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo


class ActiveSuggestionToMongo(IMapperSimple[ActiveSuggestion, dict]):
    """MongoDB mapper for `ActiveSuggestion` entities"""

    @staticmethod
    def forward(instance: ActiveSuggestion) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
            "score": instance.score,
            "models": [IDToMongo.forward(model_id) for model_id in instance.models],
            "user": instance.user,
            "reason": instance.reason,
        }

    @staticmethod
    def backward(instance: dict) -> ActiveSuggestion:
        media_identifier = MediaIdentifierToMongo.backward(instance["media_identifier"])
        models = [IDToMongo.backward(model_id) for model_id in instance["models"]]
        return ActiveSuggestion(
            id_=IDToMongo.backward(instance["_id"]),
            media_identifier=media_identifier,
            score=instance["score"],
            models=models,
            user=instance["user"],
            reason=instance["reason"],
            ephemeral=False,
        )
