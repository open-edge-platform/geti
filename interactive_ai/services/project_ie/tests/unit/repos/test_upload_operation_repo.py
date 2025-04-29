# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from entities import UploadOperation
from entities.upload_operation import FileType
from repos import UploadOperationRepo


@pytest.mark.ProjectIEMsComponent
class TestIEOperationRepo:
    def test_get_by_upload_id(self, request) -> None:
        upload_operation_repo = UploadOperationRepo()
        upload_id = "dummy_upload_id"
        operation = UploadOperation(
            id_=UploadOperationRepo.generate_id(),
            file_type=FileType.PROJECT,
            upload_id=upload_id,
            upload_parts=[],
            size=1,
            offset=0,
        )
        upload_operation_repo.save(operation)
        request.addfinalizer(lambda: upload_operation_repo.delete_by_id(operation.id_))

        reloaded_operation = upload_operation_repo.get_by_upload_id(upload_id=upload_id)
        assert reloaded_operation.upload_id == upload_id
