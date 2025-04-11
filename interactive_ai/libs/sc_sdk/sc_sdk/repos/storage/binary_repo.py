# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
This module contains the base implementation for the binary repo; the repository for binary files
"""

import io
import logging
import os
import shutil
from pathlib import Path
from typing import TypeVar

from sc_sdk.adapters.binary_interpreters import IBinaryInterpreter
from sc_sdk.utils.type_helpers import str2bool

from .local_storage import LocalStorageClient
from .object_storage import ObjectStorageClient
from .storage_client import BinaryObjectType, BinaryRepoOwnerIdentifierT, BytesStream, StorageClient
from geti_types import CTX_SESSION_VAR, ID, make_session

logger = logging.getLogger(__name__)


T = TypeVar("T")


class BinaryRepo:
    """
    The repository for binary files. The BinaryRepo stores files either in the local filesystem or in S3 object
    storage, depending on a feature flag and a predefined set of objects that S3 storage will be enabled for.
    It makes use of the StorageClient class to store objects.

    The class makes use of a registry pattern to store the default binary repos for every object type in the
    binary_repos_registry variable, so that we can easily obtain the proper binary repo for each type of object.

    Files inside the repository are identified using their filename

    :param identifier: Identifier of the object to which the data belongs
    :param organization_id: ID of organization to which above mentioned object belongs
    """

    object_type = BinaryObjectType.UNDEFINED

    def __init__(self, identifier: BinaryRepoOwnerIdentifierT, organization_id: ID | None = None) -> None:
        if self.object_type == BinaryObjectType.UNDEFINED:
            raise ValueError(
                "You forgot to override 'object_type': the binary repo cannot be "
                "instantiated without a defined object type"
            )
        self.identifier = identifier
        self.organization_id: ID
        if organization_id is not None:
            self.organization_id = organization_id
        else:
            try:
                session = CTX_SESSION_VAR.get()
            except LookupError:
                session = make_session()
            self.organization_id = session.organization_id
        self.storage_client = StorageClientFactory.acquire_storage_client(
            identifier=identifier, object_type=self.object_type, organization_id=self.organization_id
        )

    def get_path_or_presigned_url(self, filename: str, preset_headers: dict | None = None) -> Path | str:
        """
        For the file with the provided filename, get the physical path or a presigned URL for the file, depending on
        the storage type that is used.

        :param filename: Name of the file to get the path or presigned url for
        :param preset_headers: For presigned URLs, set the headers for the request. This can be used to modify the
         headers of the presigned URL's response.
        :return: Physical path or presigned URL pointing to the file
        """
        return self.storage_client.get_path_or_presigned_url(filename=filename, preset_headers=preset_headers)

    def get_by_filename(self, filename: str, binary_interpreter: IBinaryInterpreter[T]) -> T:  # type ignore
        """
        Read the binary data from the repository and parse it with a given interpreter.

        :param filename: File name of the binary file
        :param binary_interpreter: Interpreter to use to parse the data
        :return: Data read from the storage. The data format depends on the binary interpreter.
        """
        return self.storage_client.get_by_filename(filename=filename, binary_interpreter=binary_interpreter)

    def save(
        self,
        data_source: str | bytes | BytesStream | None,
        dst_file_name: str | None = None,
        remove_source: bool | None = False,
        overwrite: bool | None = True,
        make_unique: bool | None = False,
    ) -> str:
        """
        Save file or bytes data to the binary repo under the given filename

        If data is not specified, an empty file will be made.
        If the file contains previous data, it will be overwritten.

        :param dst_file_name: Filename to save the new file under
        :param data_source: Optional, bytes to save into the new file
        :param remove_source: Optional boolean, if true remove the source file
        :param overwrite: Optional boolean, if true overwrite the file, if false raise an error if the file is already
            present.
        :param make_unique: Optional boolean, if true generate a unique filename for the file to be saved under
        """
        stream_or_str: str | BytesStream
        if data_source is None:
            stream_or_str = BytesStream(data=io.BytesIO(b""), length=0)
        elif isinstance(data_source, bytes):
            stream_or_str = BytesStream(data=io.BytesIO(data_source), length=len(data_source))
        else:
            stream_or_str = data_source

        if dst_file_name is None:
            # If the name is not specified, create it from the filename or raise an error if the object has no name
            if not isinstance(stream_or_str, str):
                raise ValueError("Cannot save an unnamed file without specifying a target filename.")
            dst_file_name = os.path.basename(stream_or_str)

        filename = self.storage_client.save(
            dst_file_name=dst_file_name, data_source=stream_or_str, overwrite=overwrite, make_unique=make_unique
        )

        if remove_source and isinstance(stream_or_str, str) and os.path.exists(stream_or_str):
            try:
                os.remove(stream_or_str)
            except PermissionError:
                logger.warning(f"Attempted to remove file at {stream_or_str}, but there is no permission to do so.")
        return filename

    def save_group(self, source_directory: str) -> None:
        """
        Save a group (e.g. images, videos, models) of entities to the binary repo.

        :param source_directory: Source directory for this group of entities
        """
        self.storage_client.save_group(source_directory=source_directory)

    def export_group(self, target_directory: str) -> None:
        """
        Export a group (e.g. images, videos, models) of entities from the binary repo to the specified target directory
        This method exports all the objects in this particular binary repo.

        :param target_directory: Target directory to copy the binary entities to
        """
        self.storage_client.export_group(target_directory=target_directory)

    def delete_by_filename(self, filename: str) -> None:
        """
        Delete a binary file with the given name

        :param filename: Name of the binary file
        """
        self.storage_client.delete_by_filename(filename=filename)

    def delete_all(self) -> None:
        """
        Delete all objects in this particular binary repo
        """
        self.storage_client.delete_all()

    def get_object_size(self, filename: str) -> int:
        """
        Return the size, in bytes, of the store file

        :param filename: Name of the file to check size for
        :return: Size in bytes
        """
        return self.storage_client.get_object_size(filename=filename)

    def get_object_storage_size(self) -> float:
        """
        Return the size, in bytes, of the object storage

        :return: Size in bytes
        """
        return self.storage_client.get_object_storage_size()

    def create_path_for_temporary_file(self, filename: str, make_unique: bool) -> str:
        """
        Use the local storage client to create a temporary file location that holds a relation to the file with the
        given filename.

        :param filename: Filename of the non-temporary version of this file
        :param make_unique: Boolean indicating whether the temporary file generation should be unique or repeatable
        :return: Target filepath where a new temporary file can be created
        """
        return LocalStorageClient(
            identifier=self.identifier, object_type=self.object_type
        ).create_path_for_temporary_file(filename=filename, make_unique=make_unique)

    @staticmethod
    def get_disk_stats() -> tuple[int, int, int]:
        """
        Compute the disk usage stats for the binary repo folder
        @todo: Remove this with S3 implementation
        :return: total_storage, used_storage, free_storage in bytes
        """
        binary_repo_path = os.environ.get("WORKDIR", os.path.expanduser("~/sc_data/"))
        os.makedirs(binary_repo_path, exist_ok=True)
        total_storage, used_storage, free_storage = shutil.disk_usage(binary_repo_path)
        return total_storage, used_storage, free_storage

    def exists(self, filename: str) -> bool:
        """
        Check whether or not a file exists.

        :param filename: Name of the file to check the presence of
        :return: Boolean indicating whether or not the file exists
        """
        return self.storage_client.exists(filename=filename)


class StorageClientFactory:
    """
    StorageClientFactory is responsible for initializing a StorageClient class based on feature flag setting for
    object storage.
    """

    @staticmethod
    def acquire_storage_client(
        identifier: BinaryRepoOwnerIdentifierT, object_type: BinaryObjectType, organization_id: ID
    ) -> StorageClient:
        """
        Acquire the correct storage client based on what object type the binary repo is for, and whether or not
        the feature is enabled. Note that this pattern is a workaround, as SDK should not interact with feature flags,
        since those belong to microservices.

        :param identifier: Identifier to instantiate client with
        :param object_type: Object type this storage client is instantiate for
        :param organization_id: Organization to instantiate client with
        :return: StorageClient, that handles local or S3 storage.
        """
        enable_s3 = str2bool(os.environ.get("FEATURE_FLAG_OBJECT_STORAGE_OP", "False"))

        if enable_s3:
            return ObjectStorageClient(identifier=identifier, object_type=object_type, organization_id=organization_id)
        return LocalStorageClient(identifier=identifier, object_type=object_type)


binary_repos_registry: dict[BinaryObjectType, type[BinaryRepo]] = {}
