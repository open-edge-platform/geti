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
This module implements utility methods for the binary repo
"""

from sc_sdk.repos.storage.binary_repo import BinaryRepo, binary_repos_registry
from sc_sdk.repos.storage.storage_client import BinaryObjectType, BinaryRepoOwnerIdentifierT


def get_binary_repo(object_type: BinaryObjectType, identifier: BinaryRepoOwnerIdentifierT) -> BinaryRepo:
    """
    For the specified object type, initiate a binary repo for this object type

    :param object_type: Binary object type for which we want the binary repo
    :param identifier: Owner of this binary repo, identifier of either the project, dataset storage or model storage
    :return: BinaryRepo for the object type
    """
    binary_repo = binary_repos_registry.get(object_type, None)
    if binary_repo is None:
        raise ValueError(f"Cannot fetch binary repo for invalid object type {str(object_type)}")
    return binary_repo(identifier=identifier)
