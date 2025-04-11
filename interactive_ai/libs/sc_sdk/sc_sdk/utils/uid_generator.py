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
