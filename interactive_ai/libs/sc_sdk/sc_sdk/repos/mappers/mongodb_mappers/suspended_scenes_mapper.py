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
