#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for Dataset storage entities"""

from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo


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
