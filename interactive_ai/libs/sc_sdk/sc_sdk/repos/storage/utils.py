# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
