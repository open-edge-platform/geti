# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import logging
import os
import random
import time
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from datetime import timedelta
from functools import wraps
from io import BytesIO
from pathlib import Path

import pyarrow as pa
from minio import Minio
from minio.credentials import IamAwsProvider
from minio.datatypes import Object
from minio.deleteobjects import DeleteError, DeleteObject
from minio.error import InvalidResponseError, S3Error
from pyarrow.fs import S3FileSystem
from urllib3 import BaseHTTPResponse

from mlflow_geti_store.utils import Identifier

S3_ADDRESS = "s3.amazonaws.com"

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


class S3ObjectStorageClient:
    def __init__(self, identifier: Identifier):
        if bucket_name := os.environ.get("BUCKET_NAME_MLFLOWEXPERIMENTS", None):
            self.bucket_name = bucket_name
        else:
            msg = "Cannot find bucket name from the environment variable"
            raise RuntimeError(msg)

        self.client: Minio
        self.presigned_urls_client: Minio
        self.s3fs: S3FileSystem
        s3_credentials_provider = os.environ.get("S3_CREDENTIALS_PROVIDER")
        if s3_credentials_provider == "local":
            self.client, self.presigned_urls_client, self.s3fs = self.__authenticate_on_prem_client()
        elif s3_credentials_provider == "aws":
            self.client, self.presigned_urls_client, self.s3fs = self.__authenticate_saas_client()
        else:
            raise ValueError(
                "Environment variable S3_CREDENTIALS_PROVIDER should be set to either 'local' or 'aws' for S3 to work."
            )

        self.object_name_base = identifier.to_path()
        self.identifier = identifier
        msg = f"Initialized with object_name_base={self.object_name_base}"
        logger.info(msg)

    @staticmethod
    def __validate_environment_variables(required_variables: Sequence[str]) -> None:
        """
        Check if environment variables required for S3 are set.

        :param required_variables: A sequence of strings containing the names of the environment variables required.
        :raises ValueError: If one or more environment variables are missing.
        """
        missing_env_variables = set(required_variables) - set(os.environ)
        if missing_env_variables:
            missing_variables_str = ", ".join(missing_env_variables)
            raise ValueError(
                f"Environment variable(s) {missing_variables_str} were not set, but they are required for S3 to work."
            )

    @staticmethod
    def __authenticate_on_prem_client() -> tuple[Minio, Minio, S3FileSystem]:
        """
        Authenticate a Minio client for on-premises deployment using the credentials specified in the environment
        variables.

        :return: Tuple containing a minio client using standard secret/access key and the presigned url secret/access
        key.
        """
        S3ObjectStorageClient.__validate_environment_variables(
            required_variables=[
                "S3_ACCESS_KEY",
                "S3_SECRET_KEY",
                "S3_PRESIGNED_URL_ACCESS_KEY",
                "S3_PRESIGNED_URL_SECRET_KEY",
            ]
        )
        host_name = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        presigned_urls_client = Minio(
            endpoint=host_name,
            secure=False,
            access_key=os.environ.get("S3_PRESIGNED_URL_ACCESS_KEY", ""),
            secret_key=os.environ.get("S3_PRESIGNED_URL_SECRET_KEY", ""),
        )
        client = Minio(
            endpoint=host_name,
            secure=False,
            access_key=os.environ.get("S3_ACCESS_KEY", ""),
            secret_key=os.environ.get("S3_SECRET_KEY", ""),
        )
        s3fs = S3FileSystem(
            access_key=os.environ.get("S3_ACCESS_KEY", ""),
            secret_key=os.environ.get("S3_SECRET_KEY", ""),
            scheme="http",
            endpoint_override=host_name,
        )
        return client, presigned_urls_client, s3fs

    @staticmethod
    def __authenticate_saas_client() -> tuple[Minio, Minio, S3FileSystem]:
        """
        Authenticate a Minio client for SaaS deployment using a web identity token.
        1. Validate the required environment variables
        2. Generate the credentials by authenticating to IAM, this automatically uses the defined environment variables
        3. Initialize Minio client using these credentials.
        In SaaS, there is no distinction between normal and presigned URL credentials
        """
        S3ObjectStorageClient.__validate_environment_variables(
            required_variables=[
                "AWS_ROLE_ARN",
                "AWS_REGION",
                "AWS_WEB_IDENTITY_TOKEN_FILE",
            ]
        )

        provider = IamAwsProvider()
        client = Minio(
            endpoint=S3_ADDRESS,
            region=os.environ.get("AWS_REGION"),
            credentials=provider,
            secure=True,
        )

        credentials = provider.retrieve()
        s3fs = S3FileSystem(
            access_key=credentials.access_key,
            secret_key=credentials.secret_key,
            session_token=credentials.session_token,
            region=os.environ.get("AWS_REGION"),
            scheme="https",
        )

        return client, client, s3fs

    @retry_on_rate_limit()
    def check_file_exists(self, object_name: str) -> bool:
        try:
            self.client.stat_object(bucket_name=self.bucket_name, object_name=object_name)
        except S3Error as e:
            logger.debug(e)
            return False
        else:
            return True

    @retry_on_rate_limit()
    def save_file_from_local_disk(self, relative_path: Path, local_file_path: Path, overwrite: bool = False) -> None:
        object_name = str(self.object_name_base / relative_path)

        if not overwrite and self.check_file_exists(object_name=object_name):
            raise FileExistsError(f"Cannot save file, because a file already exists at {object_name}.")

        self.client.fput_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            file_path=str(local_file_path),
        )

    @retry_on_rate_limit()
    def save_file_from_bytes(self, relative_path: Path, input_bytes: bytes, overwrite: bool = False) -> None:
        object_name = str(self.object_name_base / relative_path)

        if not overwrite and self.check_file_exists(object_name=object_name):
            raise FileExistsError(f"Cannot save file, because a file already exists at {object_name}.")

        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=BytesIO(input_bytes),
            length=len(input_bytes),
        )

    @retry_on_rate_limit()
    def get_by_filename(self, relative_path: Path) -> BaseHTTPResponse:
        object_name = str(self.object_name_base / relative_path)

        return self.client.get_object(bucket_name=self.bucket_name, object_name=object_name)

    @retry_on_rate_limit()
    def list_files(self, relative_path: Path, recursive: bool = False) -> Iterable[Object]:
        prefix = str(self.object_name_base / relative_path)
        results = list(self.client.list_objects(bucket_name=self.bucket_name, prefix=prefix, recursive=recursive))

        if len(results) == 1:
            obj = next(iter(results))
            if obj.is_dir:
                # NOTE: The following logic is to extract depth-1 children
                # For example, if prefix has this tree file structure,
                # ├── configurations
                # ├── exportable_codes
                # ├── logs
                # │   ├── error.json
                # │   └── otx-full.log
                # └── models
                # The return list will be [prefix/configurations, prefix/exportable_codes, prefix/logs, prefix/models]
                objects = self.client.list_objects(bucket_name=self.bucket_name, prefix=prefix, recursive=True)
                rel_paths = {Path(obj.object_name).relative_to(Path(prefix)): obj for obj in objects}

                children_files = {rel_path: obj for rel_path, obj in rel_paths.items() if len(rel_path.parents) == 1}
                children_dirs = {
                    dir_name: Object(obj.bucket_name, object_name=str(Path(prefix) / dir_name) + "/")
                    for rel_path, obj in rel_paths.items()
                    if len(rel_path.parents) > 1 and (dir_name := list(reversed(rel_path.parents))[1])
                }
                children = {**children_files, **children_dirs}
                return children.values()

            # NOTE: If the query path is for a file, it should return a empty list.
            return []

        return results

    @retry_on_rate_limit()
    def delete_files(self, relative_path: Path, recursive: bool = True) -> list[DeleteError]:
        delete_object_list = [
            DeleteObject(name=obj.object_name)
            for obj in self.list_files(relative_path=relative_path, recursive=recursive)
        ]
        # NOTE: if relative_path is a file, self.list_files() returns an empty list.
        if not delete_object_list:
            delete_object_list = [DeleteObject(name=str(self.object_name_base / relative_path))]
        return list(
            self.client.remove_objects(bucket_name=self.bucket_name, delete_object_list=iter(delete_object_list))
        )

    @retry_on_rate_limit()
    def clean_all_files(self) -> list[DeleteError]:
        delete_object_list = [
            DeleteObject(name=obj.object_name)
            for obj in self.client.list_objects(
                bucket_name=self.bucket_name,
                recursive=True,
            )
        ]
        return list(
            self.client.remove_objects(bucket_name=self.bucket_name, delete_object_list=iter(delete_object_list))
        )

    @retry_on_rate_limit()
    def get_presigned_url(self, relative_path: Path) -> str:
        object_name = str(self.object_name_base / relative_path)
        return self.presigned_urls_client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            expires=timedelta(minutes=15),
        )

    def check_live_metrics_file_exists(self) -> bool:
        path = self.object_name_base / "live_metrics" / "metrics.arrow"
        return self.check_file_exists(object_name=str(path))

    @contextmanager
    def open_live_metrics_file(self) -> Iterator[pa.NativeFile]:
        path = Path(self.bucket_name) / self.object_name_base / "live_metrics" / "metrics.arrow"
        with self.s3fs.open_input_file(path=str(path)) as fp:
            yield fp

    @contextmanager
    def open_live_metrics_output_stream(self) -> Iterator[pa.NativeFile]:
        path = Path(self.bucket_name) / self.object_name_base / "live_metrics" / "metrics.arrow"
        with self.s3fs.open_output_stream(path=str(path)) as fp:
            yield fp


class S3ObjectStorageClientSingleton:
    _instance: S3ObjectStorageClient | None = None
    identifier: Identifier | None = None

    @classmethod
    def instance(cls, renew: bool = False) -> S3ObjectStorageClient:
        identifier: Identifier
        if cls.identifier is None:
            try:
                identifier = Identifier.from_config_file()
            except Exception:
                identifier = Identifier.from_env_var()
        else:
            identifier = cls.identifier
        cls.identifier = identifier

        if not renew and cls._instance:
            return cls._instance

        try:
            cls._instance = S3ObjectStorageClient(identifier=identifier)
        except Exception:
            logger.exception("Failed to initialize S3 client")
            raise
        return cls._instance
