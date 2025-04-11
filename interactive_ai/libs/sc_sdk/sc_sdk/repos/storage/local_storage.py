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
This module contains the base implementation for the storage clients, which manage the file storage for the binary
repo.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from shutil import copyfile

from sc_sdk.adapters.binary_interpreters import IBinaryInterpreter
from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.repos.storage.storage_client import BinaryObjectType, BinaryRepoOwnerIdentifierT, BytesStream, StorageClient

from geti_types import DatasetStorageIdentifier

LOCAL_STORAGE_STREAM_BATCH_SIZE = int(os.environ.get("LOCAL_STORAGE_STREAM_BATCH_SIZE", 10 * 1024 * 1024))

logger = logging.getLogger(__name__)


class LocalStorageClient(StorageClient):
    """
    This class implements the ObjectStorageClient, which is responsible for storing files to the local filesystem

    :param identifier: Identifier of the entity owning the storage
    :param object_type: Type of object to be stored in the object storage
    """

    def __init__(self, identifier: BinaryRepoOwnerIdentifierT, object_type: BinaryObjectType) -> None:
        super().__init__(identifier=identifier, object_type=object_type)
        self.base_path = self.__get_base_folder_path(owner_identifier=identifier)

    @staticmethod
    def __get_base_folder_path(owner_identifier: BinaryRepoOwnerIdentifierT) -> str:
        """
        Get the path of the folder to store items relative to the given workspace.

        :param owner_identifier: Identifier for this binary repo
        :return: Path to the folder (as string)
        """
        workdir = os.environ.get("WORKDIR", os.path.expanduser("~/sc_data/"))
        top_level_path = os.path.join(workdir, "storage/binaryrepo/")
        base_project_path = os.path.join(
            top_level_path, "workspaces", owner_identifier.workspace_id, "projects", owner_identifier.project_id
        )
        if isinstance(owner_identifier, DatasetStorageIdentifier):
            base_path = os.path.join(base_project_path, "dataset_storages", owner_identifier.dataset_storage_id)
        elif isinstance(owner_identifier, ModelStorageIdentifier):
            base_path = os.path.join(base_project_path, "model_storages", owner_identifier.model_storage_id)
        else:
            base_path = base_project_path
        return base_path

    def __get_physical_path(self, filename: str) -> str:
        """
        Get the path to a binary file for a specific file

        :param filename: filename to fetch the binary path for
        :return: Path to the location where the file is saved in the local storage system
        """
        return os.path.join(self.base_path, filename)

    def get_by_filename(self, filename: str, binary_interpreter: IBinaryInterpreter):  # noqa: ANN201
        """
        Get an object based on its name and interpret it using the binary interpreter for that file type.

        :param filename: Name used to fetch the object, consisting of name + extension.
        :param binary_interpreter: binary interpreter for this object type
        :return: Either bytes or a numpy array, depending on which binary interpreter was used.
        """
        path = self.__get_physical_path(filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"The given resource does not exist. Expected file at path `{path}`")
        if not os.path.isfile(path):
            raise FileNotFoundError(
                "The given resource does resolve to something that exists, but it is not a file. "
                f"Expected file at path `{path}`"
            )

        with open(path, "rb") as file:
            return binary_interpreter.interpret(data=file, filename=filename)

    def get_path_or_presigned_url(self, filename: str, preset_headers: dict | None = None) -> Path:  # noqa: ARG002
        """
        Get the local path where this file is stored.

        :param filename: Filename of the file the path is requested for
        :param preset_headers: Unused parameter for local storage
        :return: Path for the object at the requested URL
        """
        return Path(self.__get_physical_path(filename=filename))

    def save_file(self, filename: str, source_path: str, overwrite: bool | None) -> None:
        """
        Save a file to the local storage

        :param filename: Filename for the file to save, this will also be used to retrieve the file
        :param source_path: Current location of the file in the filesystem
        :param overwrite: Boolean, if set to true allow this method to overwrite the file present at the URL.
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Cannot save file to URL, because '{source_path}' doesn't exist.")
        target_file_path = os.path.join(self.base_path, filename)
        if not overwrite and self.exists(filename=filename):
            raise FileExistsError(f"Cannot save file to URL, because a file already exists at {target_file_path}.")

        target_folder_path = os.path.dirname(target_file_path)
        os.makedirs(target_folder_path, exist_ok=True)
        if os.path.exists(target_file_path):
            os.remove(target_file_path)
        if os.path.dirname(target_file_path) == os.path.dirname(source_path):
            os.rename(source_path, target_file_path)
            logger.debug(f"File renamed from {source_path} to {target_file_path}")
        else:
            copyfile(source_path, target_file_path)
            logger.debug(f"File copied from `{source_path}` to {target_file_path}")

    def save_bytes(self, filename: str, data: BytesStream, overwrite: bool | None):  # noqa: ANN201
        """
        Save bytes to a file with a given filename

        :param filename: Filename for the file to save, this will also be used to retrieve the file
        :param data: Raw bytes to save
        :param overwrite: Boolean, if set to true allow this method to overwrite the file present at the URL.
        """
        target_file_path = os.path.join(self.base_path, filename)
        if not overwrite and self.exists(filename=filename):
            raise FileExistsError(f"Cannot save file to URL, because a file already exists at {target_file_path}.")
        target_folder_path = os.path.dirname(target_file_path)
        os.makedirs(target_folder_path, exist_ok=True)
        with open(target_file_path, "wb") as file:
            while read_bytes := data.data().read(LOCAL_STORAGE_STREAM_BATCH_SIZE):
                file.write(read_bytes)
        logger.debug(f"Bytes written to path {target_file_path}")

    def save_group(self, source_directory: str) -> None:
        """
        Save a group (e.g. images, videos, models) of entities to the storage.

        :param source_directory: Source directory for this group of entities
        """
        try:
            os.makedirs(os.path.dirname(self.base_path), exist_ok=True)
        except OSError as exception:
            raise OSError(
                f"Cannot save binaries to target directory {self.base_path} in the binary repo."
            ) from exception
        if os.path.exists(source_directory):
            try:
                shutil.copytree(src=source_directory, dst=self.base_path, dirs_exist_ok=True)
            except OSError as exception:
                raise OSError(f"Cannot save binaries from {source_directory} to {self.base_path}") from exception

    def export_group(self, target_directory: str) -> None:
        """
        Export a group (e.g. images, videos, models) of entities from the storage to the specified target directory.
        This method exports all the objects in this particular binary repo.

        :param target_directory: Target directory to copy the binary entities to
        """
        try:
            os.makedirs(os.path.dirname(target_directory), exist_ok=True)
        except OSError as exception:
            raise OSError(f"Cannot export binaries to target directory {target_directory}") from exception
        if os.path.exists(self.base_path):
            try:
                shutil.copytree(src=self.base_path, dst=target_directory, dirs_exist_ok=True)
            except OSError as exception:
                raise OSError(f"Cannot export binaries from {self.base_path} to {target_directory}") from exception

    def delete_by_filename(self, filename: str) -> None:
        """
        Delete a file

        :param filename: Filename of the file to be deleted
        """
        if not filename:
            # skip if empty filename
            logger.warning("Skip the request to delete empty filename.")
            return

        path_to_file = self.__get_physical_path(filename=filename)
        try:
            if os.path.exists(path_to_file) and os.path.isfile(path_to_file):
                logger.debug("Removing file at %s", path_to_file)
                os.unlink(path_to_file)
        except AssertionError:
            logger.warning("Failed to delete binary at %s", path_to_file)

    def delete_all(self) -> None:
        """
        Delete all objects in this particular binary repo
        """
        if os.path.exists(self.base_path):
            shutil.rmtree(self.base_path)
        else:
            logger.warning(
                "Attempted to delete non-existing resource(s) at %s; skipping.",
                self.base_path,
            )
        # Delete parent folder only if empty
        try:
            os.rmdir(self.base_path)
            logger.debug("Deleted empty parent folder '%s'.", self.base_path)
        except (FileNotFoundError, OSError):
            pass

    def get_object_size(self, filename: str) -> int:
        """
        Measure the size of the object with the given filename

        :param filename: Name of file to measure size for.
        :return: Integer indicating the size of the object in bytes
        """
        size = 0
        if filename:
            path = self.__get_physical_path(filename=filename)
            if os.path.exists(path) and os.path.isfile(path):
                size = os.path.getsize(path)
        return size

    def get_object_storage_size(self) -> float:
        """
        Not implemented as Local Storage does not make use of S3 (Object Storage)
        """
        raise NotImplementedError

    def exists(self, filename: str) -> bool:
        """
        Check whether a file with a given filename exists

        :param filename: Filename to check presence for
        :return: Boolean indicating whether or not the file exists
        """
        return os.path.exists(self.__get_physical_path(filename=filename))

    def create_path_for_temporary_file(self, filename: str, make_unique: bool) -> str:
        """
        Create a temporary file location that holds a relation to the file at the given URL in the workspace.
        If make_unique is set to true, the temporary filepath is guaranteed to be unique. If set to false, the path
        will be generated in such a way that re-generating the path returns the same URL.

        :param filename: Filename of the non-temporary file that the temporary file relates to
        :param make_unique: If set to true, make the temporary file unique.
        :return: Target filepath where a new temporary file can be created
        """
        local_path_for_file = os.path.join(self.base_path, filename)
        _, extension = os.path.splitext(filename)
        target_directory = os.path.dirname(local_path_for_file)
        os.makedirs(target_directory, exist_ok=True)
        if make_unique:
            _, temporary_file_path = tempfile.mkstemp(suffix=extension, dir=target_directory)
        else:
            base_name, extension = os.path.splitext(local_path_for_file)
            temporary_file_path = base_name + "_tmp" + extension
        return temporary_file_path
