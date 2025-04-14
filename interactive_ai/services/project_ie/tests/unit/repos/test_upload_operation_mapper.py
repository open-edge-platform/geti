# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
