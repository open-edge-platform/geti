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
This module implements the mapper to convert DatasetItemLabels to and from
a serialized representation compatible with MongoDB
"""

from entities.dataset_item_labels import DatasetItemLabels

from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


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
