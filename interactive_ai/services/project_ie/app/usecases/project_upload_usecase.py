# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the project export usecase.
"""

import logging

from entities import UploadOperation
from repos import UploadOperationRepo
from repos.zip_storage_repo import ZipStorageRepo

from geti_types import CTX_SESSION_VAR, ID, Session

CHUNK_SIZE = 5 * 2**20

logger = logging.getLogger(__name__)


class ProjectUploadUseCase:
    """
    Coordinates the main operations for the upload process, mainly interacting with the binary repo
    and UploadOperationRepo to store uploaded files and track the upload process.
    """

    @staticmethod
    def create_multipart_upload(upload_length: int) -> ID:
        """
        Create a new multipart upload using S3 and return an operation ID for the newly created upload

        :param upload_length: Total number of bytes that need to uploaded to the file
        :return: Operation ID for the newly created upload operation
        """
        operation_id = UploadOperationRepo.generate_id()
        session: Session = CTX_SESSION_VAR.get()
        upload_id = ZipStorageRepo(
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
        ).create_multipart_upload(operation_id=operation_id)

        upload_operation = UploadOperation(
            id_=operation_id,
            upload_id=upload_id,
            upload_parts=[],
            size=upload_length,
            offset=0,
        )
        UploadOperationRepo().save(instance=upload_operation)
        return upload_operation.id_

    @staticmethod
    def get_multipart_upload_info(operation_id: ID) -> tuple[int, int]:
        """
        Obtain information about an upload operation that is in progress.

        :param operation_id: ID of the upload operation
        :return: Tuple containing
            - Size of the total upload
            - Amount of bytes already uploaded
        """
        upload_operation = UploadOperationRepo().get_by_id(id_=operation_id)
        return upload_operation.size, upload_operation.offset

    @staticmethod
    def append_to_multipart_upload(operation_id: ID, offset: int, data: bytes) -> int:
        """
        Append new bytes to an upload. Data is added in chunks defined by 'CHUNK_SIZE'. Each uploaded part needs to be
        uploaded by providing the data along with the part number, which is stored in the UploadOperation entity.
        It will return an etag for that part, which is also stored in the operation entity along with the part number.
        If all the bytes have been uploaded to the multipart upload after the part is added, a request is made to
        combine all parts, using the etags that have been stored with their part numbers.

        :param operation_id: ID of the upload operation
        :param offset: Bytes that have already previously been added to the file
        :param data: New data to be appended to the file
        :return: Number of bytes in the file after the part has been appended
        """
        session: Session = CTX_SESSION_VAR.get()
        upload_operation_repo = UploadOperationRepo()
        zip_storage_repo = ZipStorageRepo(workspace_id=session.workspace_id, organization_id=session.organization_id)
        upload_operation = upload_operation_repo.get_by_id(id_=operation_id)
        if upload_operation.offset != offset:
            raise ValueError(f"Expected offset '{upload_operation.offset}', received '{offset}' instead")

        chunk_offset = 0
        if upload_operation.upload_id is None or upload_operation.upload_parts is None:
            raise ValueError("Cannot upload parts before starting the upload operation")

        while True:
            chunk = data[chunk_offset : chunk_offset + CHUNK_SIZE]
            chunk_offset += CHUNK_SIZE
            if len(chunk) == 0:
                break
            part_number = upload_operation.compute_next_part_number()
            etag = zip_storage_repo.upload_part_to_file(
                operation_id=operation_id,
                upload_id=upload_operation.upload_id,
                part_number=part_number,
                data=chunk,
            )
            upload_operation.upload_parts.append({"ETag": etag, "PartNumber": part_number})
        new_size = len(data) + upload_operation.offset
        upload_operation.offset = new_size
        upload_operation_repo.save(instance=upload_operation)
        logger.info(
            "Appended data of size %s bytes to file with operation id %s",
            str(len(data)),
            str(operation_id),
        )
        if upload_operation.size == upload_operation.offset:
            zip_storage_repo.complete_multipart_upload(
                operation_id=upload_operation.id_,
                upload_id=upload_operation.upload_id,
                parts=upload_operation.upload_parts,
            )
        return new_size
