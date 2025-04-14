# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the base implementation for the storage clients, which manage the file storage for the binary
repo.
"""

import abc
import logging
import os
import string
import unicodedata
import uuid
from abc import ABCMeta
from enum import Enum, auto
from pathlib import Path
from typing import BinaryIO, TypeAlias, TypeVar

from sc_sdk.adapters.binary_interpreters import IBinaryInterpreter
from sc_sdk.entities.model_storage import ModelStorageIdentifier

from geti_types import DatasetStorageIdentifier, ProjectIdentifier

logger = logging.getLogger(__name__)

# BinaryRepoOwnerIdentifierT defines the identifiers of currently possible binary repo owners.
BinaryRepoOwnerIdentifierT: TypeAlias = ProjectIdentifier | ModelStorageIdentifier | DatasetStorageIdentifier

T = TypeVar("T")


class BinaryObjectType(Enum):
    """
    This Enum defines the types of objects that can be stored in the binary repo. For the S3 implementation, the string
    conversion of this enum will be the bucket name that the object will be stored under. For the local storage
    implementation, the string conversion of this enum will be the folder the object type is stored in.

    Note: some features like Project I/E depend on the names defined in this class. Removing or renaming types
    is discouraged as it can potentially break the compatibility with old exported projects; it is only allowed
    if such binary type is not included in exported archives, or if a fallback mechanism gets implemented as well.
    """

    MODELS = auto()
    IMAGES = auto()
    VIDEOS = auto()
    THUMBNAILS = auto()
    TENSORS = auto()
    RESULT_MEDIA = auto()
    CODE_DEPLOYMENTS = auto()
    MLFLOW_EXPERIMENTS = auto()
    VPS_REFERENCE_FEATURES = auto()
    UNDEFINED = auto()

    def __str__(self) -> str:
        return self.name.lower()

    def bucket_name(self) -> str:
        """Compute the bucket name string for this object type"""
        bucket_name_env_variable = "BUCKET_NAME_" + str(self).replace("_", "").upper()
        return os.environ.get(bucket_name_env_variable, str(self).replace("_", ""))

    @staticmethod
    def from_string(s: str) -> "BinaryObjectType":
        try:
            return BinaryObjectType[s.upper()]
        except KeyError:
            raise ValueError(f"'{s}' is not a valid BinaryObjectType")


class BytesStream:
    def __init__(self, data: BinaryIO, length: int):
        self.__data = data
        self.__length = length

    def length(self) -> int:
        """
        Get the length (size) of the stream
        """
        return self.__length

    def data(self) -> BinaryIO:
        """
        Get the uploaded file data
        """
        return self.__data

    def __eq__(self, other: object):  # noqa: Q000, RUF100
        if not isinstance(other, BytesStream):
            return False
        return self.__length == other.__length and self.__data == other.__data


class StorageClient(metaclass=ABCMeta):
    """
    Interface for the storage client class type containing shared methods between different storage client. A storage
    client is responsible for the file storage of the binary repo, either using S3 or the local filesystem.
    """

    def __init__(self, identifier: BinaryRepoOwnerIdentifierT, object_type: BinaryObjectType) -> None:
        self.identifier = identifier
        self.object_type = object_type

    @abc.abstractmethod
    def get_by_filename(self, filename: str, binary_interpreter: IBinaryInterpreter[T]) -> T:  # type: ignore
        """
        Fetch a file. Implemented by the child class
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_path_or_presigned_url(self, filename: str, preset_headers: dict | None = None) -> Path | str:
        """
        Get the physical path or a presigned URL for the file. Implemented by the child class.
        """
        raise NotImplementedError

    def save(
        self,
        dst_file_name: str,
        data_source: str | BytesStream,
        make_unique: bool | None = True,
        overwrite: bool | None = True,
    ) -> str:
        """
        Save a file or bytes object to the binary repo. The data source can either be the path to a file or bytes.
        This method calls the save method that will be defined in the child class, as the exact saving
        mechanic is different for different storage types.

        :param dst_file_name: Name to store the file under. This name will be parsed for invalid characters and made
            unique, if make_unique is set to true.
        :param data_source: Either a path to the file that should be saved in the binary repo, or a bytes object
        containing the binary information.
        :param make_unique: If true, check the filename formatting and make it unique by adding a unique UUID between
            the filename and the extension.
        :param overwrite: Boolean - if true, overwrite the file if it's already present. If false, raise an error
            if a file is already present.
        :return: Filename for the stored file
        """
        filename = os.path.basename(dst_file_name)
        if make_unique:
            filename = self.__create_unique_filename_for_file(filename=filename)
        if isinstance(data_source, str):
            self.save_file(filename=filename, source_path=data_source, overwrite=overwrite)
        else:
            self.save_bytes(filename=filename, data=data_source, overwrite=overwrite)
        return filename

    @abc.abstractmethod
    def save_file(self, filename: str, source_path: str, overwrite: bool | None):  # noqa: ANN201
        """
        Save a file from a given location. Implemented by the child class.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def save_bytes(self, filename: str, data: BytesStream, overwrite: bool | None):  # noqa: ANN201
        """
        Save bytes to a file with a given filename. Implemented by the child class.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def save_group(self, source_directory: str) -> None:
        """
        Save a group (e.g. images, videos, models) of entities to the storage.

        :param source_directory: Source directory for this group of entities
        """
        raise NotImplementedError

    @abc.abstractmethod
    def export_group(self, target_directory: str) -> None:
        """
        Export a group (e.g. images, videos, models) of entities from the storage to the specified target directory

        :param target_directory: Target directory to copy the binary entities to
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_by_filename(self, filename: str):  # noqa: ANN201
        """
        Delete the file with the given name. Implemented by the child class.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_all(self) -> None:
        """
        Delete all objects in this particular binary repo. Implemented by the child class
        """
        raise NotImplementedError

    @staticmethod
    def __create_unique_filename_for_file(filename: str) -> str:
        """
        Generate a unique filename for a given file. This method adds a unique UUID to the filename to enforce
        uniqueness.

        For example, an image with input filename foo.png will result in the following name:
            foo_b93b7a70-38a6-4d95-a996-a9c9f2a4a28b.png

        :param filename: Name to store the file under
        :return: Newly generated filename to save the new file at.
        """
        base_name, extension = os.path.splitext(filename)
        base_name = str(unicodedata.normalize("NFKC", base_name))
        for char in string.punctuation:
            base_name = base_name.replace(char, "_")
        replacement_chars = ["n", "t", "a", "r", "f", "v", "b"]
        for i, char in enumerate(["\n", "\t", "\a", "\r", "\f", "\v", "\b"]):
            base_name = base_name.replace(char, "_" + replacement_chars[i])
        base_name = base_name.encode("utf-8", errors="ignore").decode()
        # Insert a UID in the name
        uid = str(uuid.uuid4())
        return f"{base_name}_{uid}{extension}"

    @abc.abstractmethod
    def get_object_size(self, filename: str) -> int:
        """
        Measure the storage size of a file. Implemented by the child class.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_object_storage_size(self) -> float:
        """
        Measure the object storage. Implemented by the child class.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, filename: str) -> bool:
        """
        Check whether or not a file exists. Implemented by the child class
        """
        raise NotImplementedError

    def __deepcopy__(self, memo_dict: dict | None = None):
        # OTX makes copies of dataset items, which contain adapters with references to binary repo instances.
        # We don't need to create a new storage client for these cases.
        if memo_dict is None:
            memo_dict = {}
        memo_dict[id(self)] = self
        return self

    def __copy__(self):
        # OTX makes copies of dataset items, which contain adapters with references to binary repo instances.
        # We don't need to create a new storage client for these cases.
        return self
