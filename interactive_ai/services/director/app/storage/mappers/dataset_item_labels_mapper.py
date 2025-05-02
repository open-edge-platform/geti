# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the mapper to convert DatasetItemLabels to and from
a serialized representation compatible with MongoDB
"""

from entities.dataset_item_labels import DatasetItemLabels

from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class DatasetItemLabelsToMongo(IMapperSimple[DatasetItemLabels, dict]):
    """MongoDB mapper for `DatasetItemLabels` entities"""

    @staticmethod
    def forward(instance: DatasetItemLabels) -> dict:
        return {
            "label_ids": [IDToMongo.forward(label_id) for label_id in instance.label_ids],
            "_id": IDToMongo.forward(instance.id_),
        }

    @staticmethod
    def backward(instance: dict) -> DatasetItemLabels:
        return DatasetItemLabels(
            dataset_item_id=IDToMongo.backward(instance["_id"]),
            label_ids=[IDToMongo.backward(label_id) for label_id in instance["label_ids"]],
            ephemeral=False,
        )
