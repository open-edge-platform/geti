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

"""This module contains the MongoDB mapper for UISettings entities"""

from entities.ui_settings import UISettings

from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class UISettingsToMongo(IMapperSimple[UISettings, dict]):
    """MongoDB mapper for `UISettings` entities"""

    @staticmethod
    def forward(instance: UISettings) -> dict:
        mongo_dict = {
            "_id": IDToMongo.forward(instance.id_),
            "user_id": str(instance.user_id),
            "settings": str(instance.settings),
        }
        if instance.project_id is not None:
            mongo_dict["project_id"] = IDToMongo.forward(instance.project_id)

        return mongo_dict

    @staticmethod
    def backward(instance: dict) -> UISettings:
        return UISettings(
            id_=IDToMongo.backward(instance["_id"]),
            project_id=IDToMongo.backward(instance.get("project_id")),  # type: ignore
            user_id=instance["user_id"],
            settings=instance["settings"],
        )
