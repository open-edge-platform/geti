# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements methods for unique ID generation
"""

from bson import ObjectId

from geti_types import ID


def generate_uid() -> ID:
    """
    This function generates a unique database ID that can be assigned to entities

    NOTE: Entity ID's should ideally be generated from the repositories. This function
    should only be used in those cases where generating an ID from the appropriate
    repository is not possible, for instance in the entity definition itself
    (or similar scenarios)

    :return: unique ID
    """
    return ID(ObjectId())
