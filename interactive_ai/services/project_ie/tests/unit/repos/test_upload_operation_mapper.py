# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

import pytest

from entities.exceptions import InvalidUploadFileType
from entities.upload_operation import FileType, UploadOperation
from repos.upload_operation_mapper import UploadOperationToMongo
from repos.upload_operation_repo import UploadOperationRepo

"""
This module tests the UploadOperationMapper class.
"""


@pytest.mark.ProjectIEMsComponent
class TestUploadOperationMapper:
    def test_map_upload_operation(self) -> None:
        # Arrange
        operation = UploadOperation(
            id_=UploadOperationRepo.generate_id(),
            file_type=FileType.PROJECT,
            completed=True,
            size=100,
            offset=50,
            upload_id="dummy_id",
            upload_parts=[
                {
                    "ETag": "dummy_etag",
                    "PartNumber": 1,
                }
            ],
        )

        # Act & Assert
        serialized_entity = UploadOperationToMongo.forward(operation)
        deserialized_entity = UploadOperationToMongo.backward(serialized_entity)
        assert operation == deserialized_entity

    def test_map_upload_operation_file_type_error(self, fxt_ote_id) -> None:
        # Arrange
        doc = {
            "_id": fxt_ote_id(1),
            "file_type": "invalid_file_type",
        }

        # Act & Assert
        with pytest.raises(InvalidUploadFileType):
            UploadOperationToMongo.backward(doc)
