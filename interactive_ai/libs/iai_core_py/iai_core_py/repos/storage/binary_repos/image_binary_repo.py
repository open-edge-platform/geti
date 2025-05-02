# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for image binary files
"""

from iai_core_py.repos import BinaryRepo
from iai_core_py.repos.storage.storage_client import BinaryObjectType

from geti_types import ID, DatasetStorageIdentifier


class ImageBinaryRepo(BinaryRepo):
    """
    This module implements the repository for image binary files
    """

    object_type = BinaryObjectType.IMAGES

    def __init__(self, identifier: DatasetStorageIdentifier, organization_id: ID | None = None) -> None:
        super().__init__(identifier=identifier, organization_id=organization_id)
