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

"""This module contains the MongoDB mapper for ID entities"""

import logging
from uuid import UUID

from bson import ObjectId

from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple

from geti_types import ID


class IDToMongo(IMapperSimple[ID, ObjectId | UUID | str]):
    """MongoDB mapper for `ID` entity"""

    @staticmethod
    def forward(instance: ID) -> ObjectId | UUID | str:
        """
        The ID forward mapper forwards:
        - str of length 12 or 24 --> ObjectID
        - str of length 32 or 36 --> UUID
        - digit of arbitrary length --> pick 24 digits and converted to ObjectID
        - otherwise, return as an arbitrary string
        """
        if len(instance) in (12, 24):
            return ObjectId(str(instance))
        if len(instance) in (32, 36):
            return UUID(str(instance))
        if str(instance).isdigit():
            # ID exists of digits only. Pad with zero's to a string of length 24 (e.g.19 -> "..0019")
            id_int = int(str(instance))
            return ObjectId(f"{id_int:024d}")
        if len(instance) != 0:
            logger = logging.getLogger(__name__)
            logger.warning(f"Warning: Using str instead of ObjectId for {str(instance)}")
        return str(instance)

    @staticmethod
    def backward(instance: ObjectId | UUID | str) -> ID:
        return ID(str(instance))
