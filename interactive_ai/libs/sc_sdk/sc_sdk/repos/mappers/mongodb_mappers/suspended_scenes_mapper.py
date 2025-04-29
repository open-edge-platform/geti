# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the mapper to convert SuspendedAnnotationScenesDescriptor
entities to and from a serialized representation compatible with MongoDB
"""

from sc_sdk.entities.suspended_scenes import SuspendedAnnotationScenesDescriptor
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class SuspendedAnnotationScenesDescriptorToMongo(IMapperSimple[SuspendedAnnotationScenesDescriptor, dict]):
    """MongoDB mapper for `SuspendedAnnotationScenesDescriptor` entities"""

    @staticmethod
    def forward(instance: SuspendedAnnotationScenesDescriptor) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "scenes_ids": [IDToMongo.forward(item) for item in instance.scenes_ids],
        }

    @staticmethod
    def backward(instance: dict) -> SuspendedAnnotationScenesDescriptor:
        return SuspendedAnnotationScenesDescriptor(
            # 'project_id', 'dataset_storage_id' are from the dataset-storage-based repo
            project_id=IDToMongo.backward(instance["project_id"]),
            dataset_storage_id=IDToMongo.backward(instance["dataset_storage_id"]),
            scenes_ids=tuple(IDToMongo.backward(item) for item in instance["scenes_ids"]),
            id_=IDToMongo.backward(instance["_id"]),
        )
