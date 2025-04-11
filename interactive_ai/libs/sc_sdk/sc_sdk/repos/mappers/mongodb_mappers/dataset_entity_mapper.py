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

"""
This module implements the mapper to convert PipelineDataset to and from
a serialized representation compatible with MongoDB
"""

from sc_sdk.entities.dataset_entities import PipelineDataset, TaskDataset
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


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
