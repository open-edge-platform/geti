# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the mapper to convert PipelineDataset to and from
a serialized representation compatible with MongoDB
"""

from iai_core.entities.dataset_entities import PipelineDataset, TaskDataset
from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class PipelineDatasetToMongo(IMapperSimple[PipelineDataset, dict]):
    """MongoDB mapper for  `PipelineDataset` entities"""

    @staticmethod
    def forward(instance: PipelineDataset) -> dict:
        task_datasets_mongo = []
        for task_node_id, task_dataset in instance.task_datasets.items():
            task_datasets_mongo.append(
                {
                    "task_node_id": IDToMongo.forward(task_node_id),
                    "dataset_id": IDToMongo.forward(task_dataset.dataset_id),
                }
            )

        return {
            "project_id": IDToMongo.forward(instance.project_id),
            "task_datasets": task_datasets_mongo,
            "_id": IDToMongo.forward(instance.id_),
        }

    @staticmethod
    def backward(instance: dict) -> PipelineDataset:
        task_datasets = {
            IDToMongo.backward(task_dataset["task_node_id"]): TaskDataset(
                task_node_id=IDToMongo.backward(task_dataset["task_node_id"]),
                dataset_id=IDToMongo.backward(task_dataset["dataset_id"]),
                dataset_storage_id=IDToMongo.backward(instance["_id"]),
            )
            for task_dataset in instance["task_datasets"]
        }

        return PipelineDataset(
            project_id=IDToMongo.backward(instance["project_id"]),
            task_datasets=task_datasets,
            dataset_storage_id=IDToMongo.backward(instance["_id"]),
            ephemeral=False,
        )
