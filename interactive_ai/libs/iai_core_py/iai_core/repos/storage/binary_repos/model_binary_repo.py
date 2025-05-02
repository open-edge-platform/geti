# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for model binary files
"""

from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.repos import BinaryRepo
from iai_core.repos.storage.storage_client import BinaryObjectType

from geti_types import ID


class ModelBinaryRepo(BinaryRepo):
    """
    This module implements the repository for model binary files
    """

    object_type = BinaryObjectType.MODELS

    def __init__(self, identifier: ModelStorageIdentifier, organization_id: ID | None = None) -> None:
        super().__init__(identifier=identifier, organization_id=organization_id)
