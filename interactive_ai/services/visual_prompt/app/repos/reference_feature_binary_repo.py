# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_types import ID, ProjectIdentifier
from iai_core.repos import BinaryRepo
from iai_core.repos.storage.storage_client import BinaryObjectType


class ReferenceFeatureBinaryRepo(BinaryRepo):
    """
    ReferenceFeatureBinaryRepo is a binary repo for storing reference feature's numpy data
    """

    object_type = BinaryObjectType.VPS_REFERENCE_FEATURES

    def __init__(self, identifier: ProjectIdentifier, organization_id: ID | None = None) -> None:
        super().__init__(identifier=identifier, organization_id=organization_id)
