# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the file management usecase if object storage is enabled
"""

import logging
from typing import cast

from communication.helpers.http_exceptions import FileNotFoundGetiBaseException
from communication.repos.file_metadata_repo import FileMetadataRepo
from communication.repos.object_storage_repo import ObjectDataRepo
from domain.entities.dataset_ie_file_metadata import FileMetadata, ImportMetadata, NullFileMetadata

from geti_telemetry_tools import unified_tracing
from geti_types import ID

logger = logging.getLogger(__name__)


class FileObjectManager:
    """
    Class responsible for file management usecase if object storage is enabled.

    """

    def __init__(self) -> None:
        self.file_repo = ObjectDataRepo()
        self.metadata_repo = FileMetadataRepo()

    @unified_tracing
    def save_file(self, data: bytes) -> ID:
        """
        Save data to a new zip file in file system

        :param data: bytes to save to file system
        :return: id of the saved file
        """
        size = len(data)
        import_data = ImportMetadata(size=size, offset=size, id_=FileMetadataRepo.generate_id())
        self.metadata_repo.save(import_data)
        self.file_repo.save_file(import_data.id_, data)
        logger.info(
            "Saved data of size %s bytes to file with id %s",
            str(size),
            str(import_data.id_),
        )
        return import_data.id_

    @unified_tracing
    def create_file(self, size: int) -> ID:
        """
        Create file without saving data into it

        :param size: total size to allocate for the file
        :return: id of the created file
        """
        import_data = ImportMetadata(size=size, id_=FileMetadataRepo.generate_id())
        upload_id = self.file_repo.create_multi_upload_file(import_data.id_)
        logger.info(
            "Created file with id %s and upload id %s",
            str(import_data.id_),
            str(upload_id),
        )
        import_data.upload_id = upload_id
        import_data.upload_parts = []
        self.metadata_repo.save(import_data)
        return import_data.id_

    @unified_tracing
    def get_file_metadata(self, id_: ID) -> FileMetadata:
        """
        Get the metadata of a file in the filesystem

        :param id_: id of the file
        :return: file metadata
        """
        file_metadata = self.metadata_repo.get_by_id(id_)
        if isinstance(file_metadata, NullFileMetadata):
            logger.error("No dataset found for id %s", str(id_))
            raise FileNotFoundGetiBaseException
        return file_metadata

    @unified_tracing
    def append_to_file(self, id_: ID, data: bytes) -> int:
        """
        Append bytes of data to file in chunks. We save the data to the file in 1MB chunks to allow
        the appending to be resumed in case the operation is interrupted.

        :param id_: id of file to append the data to
        :param data: bytes to append to file in file system
        :return: new offset after appending data
        """
        chunk_size = 5 * 2**20
        i = 0
        file_metadata: ImportMetadata = cast("ImportMetadata", self.metadata_repo.get_by_id(id_))
        if file_metadata.upload_id is None or file_metadata.upload_parts is None:
            raise ValueError("Cannot upload part before starting the upload operation")

        while True:
            chunk = data[i : i + chunk_size]
            i += chunk_size
            if len(chunk) == 0:
                break
            part_number = self._get_part_number(file_metadata)
            etag = self.file_repo.upload_part_to_file(
                id_=id_,
                upload_id=file_metadata.upload_id,
                part_number=part_number,
                data=chunk,
            )
            file_metadata.upload_parts.append({"ETag": etag, "PartNumber": part_number})
        size = len(data)
        size += file_metadata.offset
        file_metadata.offset = size
        self.metadata_repo.save(file_metadata)
        logger.info(
            "Appended data of size %s bytes to file with id %s",
            str(len(data)),
            str(id_),
        )
        if file_metadata.size == file_metadata.offset:
            self.file_repo.complete_file_upload(
                id_=id_,
                upload_id=file_metadata.upload_id,
                parts=file_metadata.upload_parts,
            )
        return size

    @unified_tracing
    def delete_file(self, id_: ID) -> None:
        """
        Delete all the parts related to the upload with given id
        """
        file_metadata: ImportMetadata = cast("ImportMetadata", self.get_file_metadata(id_))
        if file_metadata.size != file_metadata.offset and file_metadata.upload_id:
            self.file_repo.abort_multi_part_upload(id_=id_, upload_id=file_metadata.upload_id)
        self.file_repo.delete_by_id(id_)
        self.metadata_repo.delete_by_id(id_)

    @staticmethod
    def _get_part_number(file_metadata: ImportMetadata) -> int:
        if file_metadata.upload_parts is None or len(file_metadata.upload_parts) == 0:
            return 1
        return max(part["PartNumber"] for part in file_metadata.upload_parts) + 1
