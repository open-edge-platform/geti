#
# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
#

"""This module contains the MongoDB mapper for Dataset storage entities"""

from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo


class DatasetStorageToMongo(IMapperSimple[DatasetStorage, dict]):
    """MongoDB mapper for `DatasetStorage` entities"""

    @staticmethod
    def forward(instance: DatasetStorage) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "name": instance.name,
            "use_for_training": instance.use_for_training,
            "creator_name": instance.creator_name,
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
        }

    @staticmethod
    def backward(instance: dict) -> DatasetStorage:
        return DatasetStorage(
            _id=IDToMongo.backward(instance["_id"]),
            # 'workspace_id' and 'project_id' are from the repo being project-based
            project_id=IDToMongo.backward(instance["project_id"]),
            name=instance["name"],
            use_for_training=instance.get("use_for_training", True),
            creator_name=instance["creator_name"],
            creation_date=DatetimeToMongo.backward(instance["creation_date"]),
            ephemeral=False,
        )
