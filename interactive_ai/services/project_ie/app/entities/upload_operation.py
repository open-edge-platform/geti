# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum

from geti_types import ID
from sc_sdk.entities.persistent_entity import PersistentEntity


class FileType(str, Enum):
    PROJECT = "project"


class UploadOperation(PersistentEntity):
    """
    Class representing metadata to track progress of an upload operation.

    :param id_: id of the operation
    :param completed: True if the upload operation has finished, False otherwise.
    :param size: total size of the file to be uploaded
    :param offset: total size of bytes already uploaded to the file
    :param upload_id: the upload id used to identify the multipart upload in S3, not an otx ID
    :param upload_parts: the parts already uploaded to the file
    :param ephemeral: True if the instance exists only in memory, False if
        it is backed up by the database
    """

    def __init__(  # noqa: PLR0913
        self,
        id_: ID,
        file_type: FileType = FileType.PROJECT,
        upload_id: str | None = None,
        completed: bool | None = False,
        size: int = 0,
        offset: int = 0,
        upload_parts: list[dict] | None = None,
        ephemeral: bool = True,
    ) -> None:
        self.completed = completed
        self.size = size
        self.offset = offset
        self.upload_id = upload_id
        self.upload_parts = upload_parts
        self.file_type = file_type
        super().__init__(id_=id_, ephemeral=ephemeral)

    def compute_next_part_number(self) -> int:
        """
        Compute the part number used in S3 for the next part that will be uploaded.
        """
        if self.upload_parts is None or len(self.upload_parts) == 0:
            return 1
        return max(part["PartNumber"] for part in self.upload_parts) + 1


class NullUploadOperation(UploadOperation):
    """
    Null entity for the UploadOperation
    """

    def __init__(self) -> None:
        super().__init__(id_=ID())

    def __repr__(self) -> str:
        return "NullUploadOperation()"
