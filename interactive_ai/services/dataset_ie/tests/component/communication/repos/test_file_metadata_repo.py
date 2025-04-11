# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
This module tests the file metadata repo
"""

from typing import TYPE_CHECKING

import pytest

from communication.mappers.file_metadata_mapper import TTL_FIELD_NAME
from communication.repos.file_metadata_repo import TTL_TIME_IN_SECONDS, FileMetadataRepo
from domain.entities.dataset_ie_file_metadata import ImportMetadata, NullFileMetadata

if TYPE_CHECKING:
    from pymongo.collection import Collection


@pytest.mark.DatasetIEMsComponent
class TestFileMetadataRepo:
    """
    unitest the file metadata repo
    """

    def test_save(self):
        file_metadata_repo = FileMetadataRepo()

        import_id = FileMetadataRepo.generate_id()
        import_data = ImportMetadata(size=10, offset=10, id_=import_id)
        file_metadata_repo.save(import_data)

        # assert if the file metadata is stored well
        file_metadata = file_metadata_repo.get_by_id(import_id)
        assert not isinstance(file_metadata, NullFileMetadata)

        assert file_metadata_repo.delete_by_id(import_id)

    def test_has_ttl_index(self):
        file_metadata_repo = FileMetadataRepo()
        collection: Collection = file_metadata_repo._collection

        # assert ttl index exists
        expire_after_seconds = None
        for index in collection.list_indexes():
            if TTL_FIELD_NAME in index["name"]:
                expire_after_seconds = index["expireAfterSeconds"]
                break
        assert expire_after_seconds == TTL_TIME_IN_SECONDS
