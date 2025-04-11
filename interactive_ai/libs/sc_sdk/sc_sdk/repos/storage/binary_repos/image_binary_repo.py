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
This module implements the repository for image binary files
"""

from sc_sdk.repos import BinaryRepo
from sc_sdk.repos.storage.storage_client import BinaryObjectType

from geti_types import ID, DatasetStorageIdentifier


class ImageBinaryRepo(BinaryRepo):
    """
    This module implements the repository for image binary files
    """

    object_type = BinaryObjectType.IMAGES

    def __init__(self, identifier: DatasetStorageIdentifier, organization_id: ID | None = None) -> None:
        super().__init__(identifier=identifier, organization_id=organization_id)
