# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
This module implements the mapper to convert UploadOperation to and from
a serialized representation compatible with MongoDB
"""

import logging

from entities.exceptions import InvalidUploadFileType
from entities.upload_operation import FileType, UploadOperation

from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

logger = logging.getLogger(__name__)


class UploadOperationToMongo(IMapperSimple[UploadOperation, dict]):
    """MongoDB mapper for `UploadOperation` entities"""

    @staticmethod
    def forward(instance: UploadOperation) -> dict:
        doc: dict = {
            "_id": IDToMongo.forward(instance.id_),
            "completed": instance.completed,
            "file_type": instance.file_type.value,
        }
        if instance.size:
            doc["size"] = instance.size
        if instance.offset:
            doc["offset"] = instance.offset
        if instance.upload_id:
            doc["upload_id"] = instance.upload_id
        if instance.upload_parts:
            doc["upload_parts"] = instance.upload_parts
        return doc

    @staticmethod
    def backward(instance: dict) -> UploadOperation:
        _file_type = instance["file_type"].upper()
        try:
            file_type = FileType[_file_type]
        except KeyError:
            raise InvalidUploadFileType(file_type=_file_type)
        return UploadOperation(
            id_=IDToMongo.backward(instance["_id"]),
            file_type=file_type,
            completed=instance["completed"],
            size=instance.get("size", 0),
            offset=instance.get("offset", 0),
            upload_id=instance.get("upload_id", ""),
            upload_parts=instance.get("upload_parts", []),
        )
