#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for ID entities"""

import logging
from uuid import UUID

from bson import ObjectId

from iai_core_py.repos.mappers.mongodb_mapper_interface import IMapperSimple

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
