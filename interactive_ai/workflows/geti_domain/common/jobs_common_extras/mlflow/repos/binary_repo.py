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
import uuid

from geti_types import ID
from minio.commonconfig import CopySource
from minio.deleteobjects import DeleteObject
from sc_sdk.repos.storage.binary_repo import BinaryRepo
from sc_sdk.repos.storage.binary_repos import ModelBinaryRepo
from sc_sdk.repos.storage.object_storage import ObjectStorageClient, reinit_client_and_retry_on_timeout
from sc_sdk.repos.storage.storage_client import BinaryObjectType

logger = logging.getLogger(__name__)


def _create_unique_name(filepath: str) -> str:
    name, ext = os.path.splitext(os.path.basename(filepath))
    suffix = uuid.uuid4()
    return f"{name}_{suffix}{ext}"


class MLFlowExperimentBinaryRepo(BinaryRepo):
    object_type = BinaryObjectType.MLFLOW_EXPERIMENTS

    def copy_from(self, model_binary_repo: ModelBinaryRepo, src_filename: str, dst_filepath: str) -> str:
        """Copy a file from the given Model binary repo to this MLFLow experiment binary repo.

        :param model_binary_repo: Model binary repo (source)
        :param src_filename: Binary filename existed in Model binary repo
        :param dst_filepath: Path of the file in this repo to be copied ('jobs/<job-id>/inputs/<filename>')
        :return: Same as dst_filepath
        """
        # NOTE: There is no interface for server-side object copy in SC-SDK.
        # This is a workaround for it. We need it because some models have
        # huge model artifacts (>500 MiB) and it makes the Flyte task
        # OOMKilled without the server-side object copy.
        # TODO: Implement a clean interface for it on the SC-SDK side.
        # CVS-133877

        model_storage_client, mlflow_storage_client = self._check_storage_clients(model_binary_repo)

        source = CopySource(
            bucket_name=model_storage_client.bucket_name,
            object_name=os.path.join(model_storage_client.object_name_base, src_filename),
        )

        # Server side copy
        mlflow_storage_client.client.copy_object(
            bucket_name=mlflow_storage_client.bucket_name,
            object_name=os.path.join(
                mlflow_storage_client.object_name_base,
                dst_filepath,
            ),
            source=source,
        )
        return dst_filepath

    def copy_to(self, model_binary_repo: ModelBinaryRepo, src_filepath: str) -> str:
        """Copy a file from this MLFLow experiment binary repo to the given Model binary repo.

        :param model_binary_repo: Model binary repo (destination)
        :param src_filepath: Path of the file in this repo to copy ('jobs/<job-id>/outputs/models/<filename>')
        :return: Filename of the copied file
        """
        # NOTE: There is no interface for server-side object copy in SC-SDK.
        # This is a workaround for it. We need it because some models have
        # huge model artifacts (>500 MiB) and it makes the Flyte task
        # OOMKilled without the server-side object copy.
        # TODO: Implement a clean interface for it on the SC-SDK side.
        # CVS-133877

        model_storage_client, mlflow_storage_client = self._check_storage_clients(model_binary_repo)

        source = CopySource(
            bucket_name=mlflow_storage_client.bucket_name,
            object_name=os.path.join(mlflow_storage_client.object_name_base, src_filepath),
        )

        dst_filename = _create_unique_name(src_filepath)

        # Server side copy
        model_storage_client.client.copy_object(
            bucket_name=model_storage_client.bucket_name,
            object_name=os.path.join(
                model_storage_client.object_name_base,
                dst_filename,
            ),
            source=source,
        )
        return dst_filename

    def _check_storage_clients(
        self, model_binary_repo: ModelBinaryRepo
    ) -> tuple[ObjectStorageClient, ObjectStorageClient]:
        """Check Both Model and this Binary Repos have ObjectStorageClient."""
        model_storage_client = model_binary_repo.storage_client
        mlflow_storage_client = self.storage_client

        if not (
            isinstance(model_storage_client, ObjectStorageClient)
            and isinstance(mlflow_storage_client, ObjectStorageClient)
        ):
            msg = "Both Model and MLFlow storage clients should be ObjectStorageClient."
            raise TypeError(msg)

        return model_storage_client, mlflow_storage_client

    # TODO CVS-133311 apply retry on rate limit after refactoring
    @reinit_client_and_retry_on_timeout
    def delete_all_under_job_dir(self, job_id: ID) -> None:
        """Delete all objects under `mlflowexperiments/.../jobs/<job-id>` directory.

        :param job_id: Job ID of directory to remove.
        """
        if not isinstance(self.storage_client, ObjectStorageClient):
            logger.warning("Only ObjectStorageClient is available for delete all under job dir.")
            return

        client = self.storage_client.client
        bucket_name = self.storage_client.bucket_name

        prefix = os.path.join(self.storage_client.object_name_base, "jobs", str(job_id))

        delete_object_list = (
            DeleteObject(x.object_name) for x in client.list_objects(bucket_name, prefix=prefix, recursive=True)
        )
        errors = client.remove_objects(bucket_name, delete_object_list=delete_object_list)
        for error in errors:
            logger.error("An error occurred when deleting object: %s", error)
