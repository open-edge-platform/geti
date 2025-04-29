# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from minio.deleteobjects import DeleteObject

from sc_sdk.repos.storage.binary_repo import BinaryRepo
from sc_sdk.repos.storage.object_storage import ObjectStorageClient, reinit_client_and_retry_on_timeout
from sc_sdk.repos.storage.storage_client import BinaryObjectType

logger = logging.getLogger(__name__)


class MLFlowBinaryRepo(BinaryRepo):
    object_type = BinaryObjectType.MLFLOW_EXPERIMENTS

    # TODO CVS-133311 apply retry on rate limit after refactoring
    @reinit_client_and_retry_on_timeout
    def delete_all_under_project_dir(self) -> None:
        """
        Delete all objects under `mlflowexperiments/.../projects/<project-id>` prefix.
        The project ID is taken from the ProjectIdentifier used to initialise this class.
        """
        # TODO CVS-126421 Clean up object storage code CVS-126421
        if not isinstance(self.storage_client, ObjectStorageClient):
            msg = "Only ObjectStorageClient is available."
            raise TypeError(msg)

        client = self.storage_client.client
        bucket_name = self.storage_client.bucket_name
        prefix = self.storage_client.object_name_base

        delete_object_list = (
            DeleteObject(x.object_name) for x in client.list_objects(bucket_name, prefix=prefix, recursive=True)
        )
        errors = client.remove_objects(bucket_name, delete_object_list=delete_object_list)
        for error in errors:
            logger.error("An error occurred when deleting object: %s", error)
