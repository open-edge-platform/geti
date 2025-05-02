# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the mapper to convert DatasetItemCount to and from
a serialized representation compatible with MongoDB
"""

from entities.dataset_item_count import DatasetItemCount, LabelData

from iai_core_py.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class DatasetItemCountToMongo(IMapperSimple[DatasetItemCount, dict]):
    """MongoDB mapper for `DatasetItemCount` entities"""

    @staticmethod
    def forward(instance: DatasetItemCount) -> dict:
        label_data_mongo = [
            {
                "_id": IDToMongo.forward(label_data.id_),
                "name": label_data.name,
                "color": label_data.color_hex_str,
                "is_anomalous": label_data.is_anomalous,
            }
            for label_data in instance.task_label_data
        ]
        return {
            "task_label_data": label_data_mongo,
            "n_dataset_items": instance.n_dataset_items,
            "n_items_per_label": [
                {"label_id": IDToMongo.forward(label_id), "n_items": n_items}
                for label_id, n_items in instance.n_items_per_label.items()
            ],
            "unassigned_dataset_items": [
                IDToMongo.forward(dataset_item_id) for dataset_item_id in instance.unassigned_dataset_items
            ],
            "_id": IDToMongo.forward(instance.id_),
        }

    @staticmethod
    def backward(instance: dict) -> DatasetItemCount:
        label_data = [
            LabelData(
                id_=IDToMongo.backward(label_data_mongo["_id"]),
                name=label_data_mongo["name"],
                color_hex_str=label_data_mongo["color"],
                is_anomalous=label_data_mongo["is_anomalous"],
            )
            for label_data_mongo in instance["task_label_data"]
        ]

        return DatasetItemCount(
            task_node_id=IDToMongo.backward(instance["_id"]),
            task_label_data=label_data,
            n_dataset_items=instance["n_dataset_items"],
            n_items_per_label={
                IDToMongo.backward(per_label_dict["label_id"]): per_label_dict["n_items"]
                for per_label_dict in instance["n_items_per_label"]
            },
            unassigned_dataset_items=[
                IDToMongo.backward(dataset_item_id) for dataset_item_id in instance["unassigned_dataset_items"]
            ],
            ephemeral=False,
        )
