# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the base implementation for the storage clients, which manage the file storage for the binary
repo.
"""

import io
import logging
import os
import random
import time
from collections.abc import Callable
from datetime import timedelta
from functools import wraps

import numpy as np
import urllib3.exceptions
from minio import Minio
from minio.deleteobjects import DeleteObject
from minio.error import InvalidResponseError, S3Error

from sc_sdk.adapters.binary_interpreters import IBinaryInterpreter
from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.repos.storage.s3_connector import S3Connector
from sc_sdk.repos.storage.storage_client import BinaryObjectType, BinaryRepoOwnerIdentifierT, BytesStream, StorageClient

from geti_types import ID, DatasetStorageIdentifier

logger = logging.getLogger(__name__)


def retry_on_rate_limit(initial_delay: float = 1.0, max_retries: int = 5, max_backoff: float = 20.0) -> Callable:
    """
    Decorator to automatically retry a method using exponential back-off strategy.
    If the decorated method raises an InvalidResponseError with error code 429 or 503, it will be retried up to 5 times.
    The delay between requests increases exponentially with jitter, similar to AWS SDK implementation:
    https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html
    This is useful to avoid breaking the current operation when the rate limit is hit. When the called method fails due
    to a 429 or 503 error, it is tried again after a short time.

    :param initial_delay: Initial delay in seconds before retrying after a 429 or 503 error
    :param max_retries: Maximum number of retries
    :param max_backoff: Maximum backoff time in seconds
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except InvalidResponseError as e:
                    if e._code not in (429, 503):
                        raise

                    # ruff: noqa: S311
                    jitter = random.uniform(0, 1)  # nosec
                    backoff_time = min(jitter * (2**retries) * delay, max_backoff)
                    time.sleep(backoff_time)
                    retries += 1

            raise RuntimeError(
                f"Max retries reached for function {func.__name__} after receiving 429 or 503 response "
                f"{retries} times in a row."
            )

        return wrapper

    return decorator


def reinit_client_and_retry_on_timeout(func: Callable) -> Callable:
    """
    Retry the method if it fails due to a urllib.TimeoutError, after re-initializing the S3 client.
    Usually such errors indicate a connection problem (e.g. dead connection), so refreshing the client may help.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):  # noqa: ANN001
        try:
            return func(self, *args, **kwargs)
        except urllib3.exceptions.TimeoutError:
            logger.exception("S3 operation failed due TimeoutError; reinitializing the client and retrying.")
            # Refresh the client after invalidating the cache
            S3Connector.clear_client_cache()
            self.client, self.presigned_urls_client = S3Connector.get_clients()
            # Retry once
            return func(self, *args, **kwargs)

    return wrapper


class ObjectStorageClient(StorageClient):
    """
    This class implements the ObjectStorageClient, which is responsible for storing files to S3 object storage.

    :param identifier: Identifier of the entity owning the storage
    :param object_type: Type of object to be stored in the object storage
    :param organization_id: ID of the organization owning the storage
    """

    def __init__(
        self, identifier: BinaryRepoOwnerIdentifierT, object_type: BinaryObjectType, organization_id: ID
    ) -> None:
        super().__init__(identifier=identifier, object_type=object_type)
        self._client, self._presigned_urls_client = S3Connector.get_clients()
        self.bucket_name = object_type.bucket_name()
        self.object_name_base = self.__get_object_name_base(
            owner_identifier=identifier, organization_id=organization_id
        )
        self._pid = os.getpid()

    @property
    def client(self) -> Minio:
        """Get Minio client. If current process doesn't make own instance, get new client."""
        cur_pid = os.getpid()
        if self._pid != cur_pid:
            self._pid = cur_pid
            self._client, self._presigned_urls_client = S3Connector.get_clients()
        return self._client

    @property
    def presigned_urls_client(self) -> Minio:
        """Get Minio presigned url client. If current process doesn't make own instance, get new client."""
        cur_pid = os.getpid()
        if self._pid != cur_pid:
            self._pid = cur_pid
            self._client, self._presigned_urls_client = S3Connector.get_clients()
        return self._presigned_urls_client

    @staticmethod
    def __get_object_name_base(owner_identifier: BinaryRepoOwnerIdentifierT, organization_id: ID):  # noqa: ANN205
        """
        Get the object name base for this repo: the base path where objects are stored from the base of the bucket.
        Example of an object name base as it might currently look:
            organizations/000000000000000000000001/workspaces/63B183D00000000000000001/projects/
            63B183D00000000000000002/dataset_storages/63B183D00000000000000003/

        The object name base consists of:
         - The configuration-defined base path, which is the top level directory as it is defined in the configuration
            of the microservice: this is for example the cell ID the microservice belongs to. The backend does not need
            to concern itself with this, and for on-prem the value is an empty string.
         - The organization ID
         - The workspace and project ID
         - If the identifier is a model storage or dataset storage identifier, the ID for that identifier.
        """
        config_defined_base_path = os.environ.get("OBJECT_STORAGE_BASE_PATH", "")
        base_project_path = os.path.join(
            config_defined_base_path,
            "organizations",
            str(organization_id),
            "workspaces",
            str(owner_identifier.workspace_id),
            "projects",
            str(owner_identifier.project_id),
        )
        if isinstance(owner_identifier, DatasetStorageIdentifier):
            object_name_base = os.path.join(base_project_path, "dataset_storages", owner_identifier.dataset_storage_id)
        elif isinstance(owner_identifier, ModelStorageIdentifier):
            object_name_base = os.path.join(base_project_path, "model_storages", owner_identifier.model_storage_id)
        else:
            object_name_base = base_project_path
        return object_name_base

    @retry_on_rate_limit()
    @reinit_client_and_retry_on_timeout
    def get_by_filename(self, filename: str, binary_interpreter: IBinaryInterpreter) -> bytes | np.ndarray:
        """
        Get an object based on its name and interpret it using the binary interpreter for that file type.

        :param filename: Name used to fetch the object, consisting of name + extension.
        :param binary_interpreter: binary interpreter for this object type
        :return: Either bytes or a numpy array, depending on which binary interpreter was used.
        """
        object_name = os.path.join(self.object_name_base, filename)
        try:
            obj = self.client.get_object(bucket_name=self.bucket_name, object_name=object_name)
            return binary_interpreter.interpret(io.BytesIO(obj.data), filename=filename)
        except urllib3.exceptions.SSLError:
            logger.warning(f"Could not load data for file {filename} due to an SSL error. Retrying once more.")
            obj = self.client.get_object(bucket_name=self.bucket_name, object_name=object_name)
            return binary_interpreter.interpret(io.BytesIO(obj.data), filename=filename)
        except S3Error as e:
            logger.error(f"The given resource does not exist. Expected file to be present at {object_name}: {e}")
            raise FileNotFoundError(f"The given resource does not exist. Expected file to be present at {object_name}")

    def get_path_or_presigned_url(self, filename: str, preset_headers: dict | None = None) -> str:
        """
        Generate a presigned URL for the object described by the given filename. This presigned URL can be used by
        features such as ffmpeg to easily fetch and manipulate the file.

        :param filename: Filename used to retrieve the file for which we want to create a presigned url
        :param preset_headers: Preset headers for the presigned URL to override the standard headers
        :return: Presigned URL for the object
        """
        object_name = os.path.join(self.object_name_base, filename)
        return self.presigned_urls_client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            expires=timedelta(minutes=15),
            response_headers=preset_headers,
        )

    @retry_on_rate_limit()
    @reinit_client_and_retry_on_timeout
    def save_file(self, filename: str, source_path: str, overwrite: bool | None) -> None:
        """
        Save a file to the object storage

        :param filename: Filename for the file to save, this will also be used to retrieve the file
        :param source_path: Current location of the file in the filesystem
        :param overwrite: Boolean, if set to true allow this method to overwrite the file present
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Cannot save file, because '{source_path}' doesn't exist.")
        object_name = os.path.join(self.object_name_base, filename)
        if not overwrite and self.exists(filename=filename):
            raise FileExistsError(f"Cannot save file, because a file already exists at {object_name}.")
        self.client.fput_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            file_path=source_path,
        )

    @retry_on_rate_limit()
    @reinit_client_and_retry_on_timeout
    def save_bytes(self, filename: str, data: BytesStream, overwrite: bool | None) -> None:
        """
        Save bytes to an object with a given filename

        :param filename: Filename for the file to save, this will also be used to retrieve the file
        :param data: Raw bytes data to save
        :param overwrite: Boolean, if set to true allow this method to overwrite the file present
        """
        object_name = os.path.join(self.object_name_base, filename)
        if not overwrite and self.exists(filename=filename):
            raise FileExistsError(f"Cannot save file, because a file already exists at {object_name}.")
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=data.data(),
            length=data.length(),
        )

    # TODO CVS-133311 apply retry on rate limit after refactoring
    @reinit_client_and_retry_on_timeout
    def save_group(self, source_directory: str) -> None:
        """
        Save a group (e.g. images, videos, models) of entities to the S3 storage.

        :param source_directory: Source directory for this group of entities
        """
        if not os.path.exists(source_directory):
            raise NotADirectoryError("Could not find the source directory of binaries to save to S3 storage")
        self.__upload_local_directory_to_s3(
            source_directory=source_directory,
            bucket_name=self.bucket_name,
            prefix=self.object_name_base,
        )

    def __upload_local_directory_to_s3(self, source_directory: str, bucket_name: str, prefix: str) -> None:
        """
        Upload the contents of a source directory to S3. This method recursively uploads any files in nested folders
        as well.

        :param source_directory: Source directory to be uploaded to S3
        :param bucket_name: Bucket name of the S3 bucket
        :param prefix: Prefix for the file to be uploaded, this is the same as the path from the workspace root.
        """
        for file_or_folder in os.listdir(source_directory):
            file_or_folder_path = os.path.join(source_directory, file_or_folder)
            file_or_folder_s3_path = os.path.join(prefix, file_or_folder)
            if os.path.isfile(file_or_folder_path):
                self.client.fput_object(
                    bucket_name=bucket_name,
                    object_name=file_or_folder_s3_path,
                    file_path=file_or_folder_path,
                )
            else:
                self.__upload_local_directory_to_s3(
                    source_directory=file_or_folder_path,
                    bucket_name=bucket_name,
                    prefix=file_or_folder_s3_path,
                )

    # TODO CVS-133311 apply retry on rate limit after refactoring
    @reinit_client_and_retry_on_timeout
    def export_group(self, target_directory: str) -> None:
        """
        Export a group (e.g. images, videos, models) of entities from the storage to the specified target directory.
        This method exports all the objects in this particular binary repo.

        :param target_directory: Target directory to copy the binary entities to
        """
        logger.info(f"Exporting {self.object_name_base} to {target_directory}")
        if self.client.bucket_exists(self.bucket_name):
            objects_to_fetch = self.client.list_objects(
                bucket_name=self.bucket_name, prefix=self.object_name_base + "/"
            )
            for s3_object in objects_to_fetch:
                # Get the object name from the owner path onward. This usually consists of the filename and the
                # extension. Remove slashes from the name and use this name as filename for the saved file.
                object_name_from_owner = s3_object.object_name.replace(self.object_name_base, "").replace("/", "")
                target_location = os.path.join(target_directory, object_name_from_owner)
                try:
                    os.makedirs(os.path.dirname(target_directory), exist_ok=True)
                except OSError as exception:
                    raise OSError(
                        f"Cannot save binaries from S3 object name {s3_object.object_name} to {target_directory}"
                    ) from exception
                self.client.fget_object(
                    bucket_name=self.bucket_name,
                    file_path=target_location,
                    object_name=s3_object.object_name,
                )

    @retry_on_rate_limit()
    @reinit_client_and_retry_on_timeout
    def delete_by_filename(self, filename: str) -> None:
        """
        Delete a file

        :param filename: Filename of the file to be deleted
        """
        object_name = os.path.join(self.object_name_base, filename)
        self.client.remove_object(bucket_name=self.bucket_name, object_name=object_name)

    # TODO CVS-133311 apply retry on rate limit after refactoring
    @reinit_client_and_retry_on_timeout
    def delete_all(self) -> None:
        """
        Delete all objects in this particular binary repo
        """
        delete_object_list = (
            DeleteObject(x.object_name)
            for x in self.client.list_objects(self.bucket_name, prefix=self.object_name_base + "/", recursive=True)
        )
        errors = self.client.remove_objects(self.bucket_name, delete_object_list=delete_object_list)
        for error in errors:
            logger.error("An error occured when deleting object: %s", error)

    @retry_on_rate_limit()
    @reinit_client_and_retry_on_timeout
    def get_object_size(self, filename: str) -> int:
        """
        Measure the size of the object with the given filename

        :param filename: Name of file to measure size for.
        :return: Integer indicating the size of the object in bytes
        """
        object_name = os.path.join(self.object_name_base, filename)
        try:
            obj = self.client.stat_object(bucket_name=self.bucket_name, object_name=object_name)
            return obj.size
        except S3Error as e:
            logger.debug(e)
            return 0

    @retry_on_rate_limit()
    @reinit_client_and_retry_on_timeout
    def get_object_storage_size(self) -> float:
        """
        Calculate the total size for all objects in the object storage

        :return: Float indicating the total size of the object storage in bytes
        """
        objects = self.client.list_objects(
            bucket_name=self.bucket_name,
            prefix=self.object_name_base + "/",
            recursive=True,
        )
        return sum(obj.size for obj in objects)

    @retry_on_rate_limit()
    @reinit_client_and_retry_on_timeout
    def exists(self, filename: str) -> bool:
        """
        Check whether an object with a given filename exists

        :param filename: Filename to check presence for
        :return: Boolean indicating whether or not the file exists
        """
        try:
            object_name = os.path.join(self.object_name_base, filename)
            self.client.stat_object(bucket_name=self.bucket_name, object_name=object_name)
            return True
        except S3Error as e:
            logger.debug(e)
            return False
