# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

import logging
import os
from collections.abc import Sequence
from threading import Lock

from cachetools import TTLCache, cached
from minio import Minio
from minio.credentials import IamAwsProvider

S3_ADDRESS = "s3.amazonaws.com"
S3_CLIENT_CACHE_TTL = int(os.environ.get("S3_CLIENT_CACHE_TTL", 3600))

logger = logging.getLogger(__name__)


class S3Connector:
    @staticmethod
    def __validate_environment_variables(required_variables: Sequence[str]) -> None:
        """
        Check if environment variables required for S3 are set.

        :param required_variables: A sequence of strings containing the names of the environment variables required.
        :raises OSError: If one or more environment variables are missing.
        """
        missing_env_variables = set(required_variables) - set(os.environ)
        if missing_env_variables:
            missing_variables_str = ", ".join(missing_env_variables)
            raise OSError(
                f"Environment variable(s) {missing_variables_str} were not set, but they are required for S3 to work."
            )

    @staticmethod
    def __authenticate_on_prem_client() -> tuple[Minio, Minio]:
        """
        Authenticate a Minio client for on-premises deployment using the credentials specified in the environment
        variables.

        :return: Tuple containing a minio client using standard secret/access key and the presigned url secret/access
        key.
        """
        S3Connector.__validate_environment_variables(
            required_variables=[
                "S3_ACCESS_KEY",
                "S3_SECRET_KEY",
                "S3_PRESIGNED_URL_ACCESS_KEY",
                "S3_PRESIGNED_URL_SECRET_KEY",
            ]
        )
        host_name = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        logger.info("Authenticating to S3 (%s) through access key; TLS disabled", host_name)
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
        return client, presigned_urls_client

    @staticmethod
    def __authenticate_saas_client() -> tuple[Minio, Minio]:
        """
        Authenticate a Minio client for SaaS deployment using a web identity token.
          1. Validate the required environment variables
          2. Generate the credentials by authenticating to IAM, this automatically uses the defined env variables
          3. Initialize Minio client using these credentials.
        Note: In SaaS, there is no distinction between normal and pre-signed URL credentials
        """
        S3Connector.__validate_environment_variables(
            required_variables=[
                "AWS_ROLE_ARN",
                "AWS_REGION",
                "AWS_WEB_IDENTITY_TOKEN_FILE",
            ]
        )
        logger.info("Authenticating to S3 (%s) through IAM; TLS enabled", S3_ADDRESS)
        client = Minio(
            endpoint=S3_ADDRESS,
            region=os.environ.get("AWS_REGION"),
            credentials=IamAwsProvider(),
            secure=True,
        )
        return client, client

    @staticmethod
    @cached(cache=TTLCache(maxsize=1, ttl=S3_CLIENT_CACHE_TTL), lock=Lock())
    def _get_clients(pid: int) -> tuple[Minio, Minio]:  # noqa: ARG004
        """
        Get Minio clients to connect to S3 with regular and pre-signed URL credentials, respectively.

        This method exploits a TTL cache to avoid creating redundant connections.

        :param pid: Process ID. This argument, although apparently unused in the method body, is actually necessary
            to force the cache to return different clients after a multiprocessing fork(),
            since Minio is not thread-safe between different processes.
        :return: two Minio clients; the first should be used for regular fetch/store interactions
            with the object storage, while the second one should be exclusively used to create pre-signed URLs.
        """
        s3_credentials_provider = os.environ.get("S3_CREDENTIALS_PROVIDER")
        logger.info("Initializing new Minio S3 client ('%s' credentials)", s3_credentials_provider)
        match s3_credentials_provider:
            case "local":
                return S3Connector.__authenticate_on_prem_client()
            case "aws":
                return S3Connector.__authenticate_saas_client()
            case _:
                raise OSError(
                    "Environment variable S3_CREDENTIALS_PROVIDER should be set to either 'local' "
                    "or 'aws' for S3 to work."
                )

    @staticmethod
    def get_clients() -> tuple[Minio, Minio]:
        """
        Get Minio clients to connect to S3 with regular and pre-signed URL credentials, respectively.

        This method exploits a TTL cache to avoid creating redundant connections.
        The method is also thread-safe.

        :return: two Minio clients; the first should be used for regular fetch/store interactions
            with the object storage, while the second one should be exclusively used to create pre-signed URLs.
        """
        # always get the process ID, so the client can be reinitialized in case of fork
        pid = os.getpid()
        return S3Connector._get_clients(pid)

    @staticmethod
    def clear_client_cache() -> None:
        S3Connector._get_clients.cache_clear()  # type: ignore
