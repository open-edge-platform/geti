# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module defines the FileMetadata class
"""

from enum import Enum, IntFlag, auto

from geti_types import ID
from sc_sdk.entities.persistent_entity import PersistentEntity


class ExportState(IntFlag):
    """
    Export state, reflects the different stages of export
    """

    STARTING = auto()
    EXPORTING = auto()
    ZIPPING = auto()
    DONE = auto()
    ERROR = auto()


class ExportFormat(Enum):
    COCO = "coco"
    YOLO = "yolo"
    VOC = "voc"
    DATUMARO = "datumaro"


class FileMetadata(PersistentEntity):
    """
    Class representing the metadata for a file in the file system.

    :param id_: id of the file
    :param size: total size of the file in bytes
    :param offset: number of bytes already saved to the file
    :param project_id: id of project related to this dataset
    """

    def __init__(
        self,
        id_: ID,
        size: int = 0,
        offset: int = 0,
        project_id: ID | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=id_, ephemeral=ephemeral)
        self.size = size
        self.offset = offset
        self.project_id = project_id if project_id is not None else ID()


class NullFileMetadata(FileMetadata):
    """
    Null entity for the FileMetadata
    """

    def __init__(self) -> None:
        super().__init__(id_=ID())

    def __repr__(self) -> str:
        return "NullFileMetadata()"


class ExportMetadata(FileMetadata):
    """
    Class representing the metadata for a file in the file system.

    :param id_: id of the file
    :param size: total size of the file in bytes
    :param offset: number of bytes already saved to the file
    :param project_id: id of project related to this dataset
    """

    def __init__(
        self,
        id_: ID,
        size: int = 0,
        offset: int = 0,
        project_id: ID | None = None,
    ) -> None:
        super().__init__(
            size=size,
            offset=offset,
            id_=id_,
            project_id=project_id,
        )


class ImportMetadata(FileMetadata):
    """
    Class representing the metadata for a file in the file system.

    :param id_: id of the file
    :param size: total size of the file in bytes
    :param offset: number of bytes already saved to the file
    :param upload_id: id of the upload operation to object storage
    :param upload_parts: list of info about upload parts to object storage
    :param project_id: id of project related to this dataset
    """

    def __init__(
        self,
        id_: ID,
        size: int = 0,
        offset: int = 0,
        upload_id: str | None = None,
        upload_parts: list[dict] | None = None,
        project_id: ID | None = None,
    ) -> None:
        super().__init__(
            size=size,
            offset=offset,
            id_=id_,
            project_id=project_id,
        )
        self.upload_id = upload_id
        self.upload_parts = upload_parts
