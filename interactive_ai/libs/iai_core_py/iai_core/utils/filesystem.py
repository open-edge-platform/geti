# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Utility functions that deal with file-system"""

import os

from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.entities.project import Project
from iai_core.repos import BinaryRepo, ModelStorageRepo
from iai_core.repos.storage.binary_repos import (
    CodeDeploymentBinaryRepo,
    ImageBinaryRepo,
    ModelBinaryRepo,
    TensorBinaryRepo,
    ThumbnailBinaryRepo,
    VideoBinaryRepo,
)
from iai_core.utils.feature_flags import FeatureFlagProvider
from iai_core.utils.timed_lru_cache import timed_lru_cache

from geti_types import DatasetStorageIdentifier

FEATURE_FLAG_STORAGE_SIZE_COMPUTATION = "FEATURE_FLAG_STORAGE_SIZE_COMPUTATION"

# The 10GiB is selected, considering the log is adding 1GiB per day, the user will have
# 10 days until the system becomes unusable.
MIN_FREE_SPACE_GIB = int(os.environ.get("MIN_FREE_SPACE_GIB", 5)) + 10

MSG_ERR_CANNOT_UPLOAD = (
    "Cannot upload media of size {upload_size_gib:.2f} GiB when only {free_space_gib:.2f}GB is available: "
    "{min_free_space_after_upload_gib:.2f} GB of space must be kept free"
)
MSG_ERR_NOT_ENOUGH_SPACE = (
    "Cannot perform operation '{operation}' when there is {free_space_gib:.2f}GB "
    "of storage space left. At least {min_free_space_for_operation}GB "
    "should be available."
)


@timed_lru_cache(seconds=30)
def compute_project_size(project: Project) -> float:
    """
    Computes the size of the data in the project. This includes data such as model
    storages, dataset storages and project storage. Value is only recomputed if it
    hasn't been computed in the last 5 minutes.

    :param project: Project to calculate the size for
    :return: project size in bytes
    """
    total_size = 0.0

    # Add the size of all the dataset storage directories
    for dataset_storage_id in project.dataset_storage_ids:
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage_id,
        )
        total_size += ImageBinaryRepo(dataset_storage_identifier).get_object_storage_size()
        total_size += VideoBinaryRepo(dataset_storage_identifier).get_object_storage_size()
        total_size += ThumbnailBinaryRepo(dataset_storage_identifier).get_object_storage_size()
        total_size += TensorBinaryRepo(dataset_storage_identifier).get_object_storage_size()

    # Add the size of all the model storage directories
    for training_task_node in project.get_trainable_task_nodes():
        model_storages = ModelStorageRepo(project.identifier).get_by_task_node_id(training_task_node.id_)
        for model_storage in model_storages:
            model_storage_identifier = ModelStorageIdentifier(
                workspace_id=project.workspace_id, project_id=project.id_, model_storage_id=model_storage.id_
            )
            total_size += ModelBinaryRepo(model_storage_identifier).get_object_storage_size()

    # Add the size of extra project files
    total_size += CodeDeploymentBinaryRepo(project.identifier).get_object_storage_size()

    return total_size


def check_free_space_for_upload(
    upload_size: int,
    exception_type: type[Exception],
    min_free_space_after_upload_gib: float = MIN_FREE_SPACE_GIB,
) -> None:
    """
    Check if there is enough space in the filesystem to perform an upload operation.

    :param upload_size: Size in bytes of the file to upload
    :param exception_type: Type of exception to raise if not enough space is available
    :param min_free_space_after_upload_gib: Optional, minimum number of GiB that should
        remain free even after completing the upload operation
    :raises: Exception (defined by exception_type) if there is not enough space to
        accommodate the file to upload while leaving a min amount of free space.
    """
    if FeatureFlagProvider.is_enabled(FEATURE_FLAG_STORAGE_SIZE_COMPUTATION):
        free_space_gib: float = float(BinaryRepo.get_disk_stats()[2]) / 2**30
        upload_size_gib: float = upload_size / (2**30)
        if upload_size_gib > free_space_gib - min_free_space_after_upload_gib:
            message = MSG_ERR_CANNOT_UPLOAD.format(
                upload_size_gib=round(upload_size_gib, 2),
                free_space_gib=round(free_space_gib, 2),
                min_free_space_after_upload_gib=round(min_free_space_after_upload_gib, 2),
            )
            raise exception_type(message)


def _has_free_space_for_operation(
    operation: str,
    min_free_space_for_operation: float = 5.0,
) -> tuple[bool, str | None]:
    """
    Helper method to check if there is enough space in the filesystem to perform an operation.

    :param operation: The type of operation to be completed
    :param min_free_space_for_operation: Optional, minimum number of GiB that should
        be available so that the operation can take place
    :return: A tuple containing a boolean indicating if there is enough space and a message
    """
    if FeatureFlagProvider.is_enabled(FEATURE_FLAG_STORAGE_SIZE_COMPUTATION):
        free_space_gib: float = float(BinaryRepo.get_disk_stats()[2]) / 2**30
        if free_space_gib < min_free_space_for_operation:
            message = MSG_ERR_NOT_ENOUGH_SPACE.format(
                operation=operation,
                free_space_gib=free_space_gib,
                min_free_space_for_operation=min_free_space_for_operation,
            )
            return False, message
    return True, None


def check_free_space_for_operation(
    operation: str,
    exception_type: type[Exception],
    min_free_space_for_operation: float = MIN_FREE_SPACE_GIB,
) -> None:
    """
    Check if there is enough space in the filesystem to perform an operation.

    :param operation: The type of operation to be completed
    :param exception_type: Type of exception to raise if not enough space is available
    :param min_free_space_for_operation: Optional, minimum number of GiB that should
        be available so that the operation can take place
    :raises: Exception (defined by exception_type) if there is not enough space to
        complete the operation.
    """
    has_space, message = _has_free_space_for_operation(
        operation=operation,
        min_free_space_for_operation=min_free_space_for_operation,
    )
    if not has_space:
        raise exception_type(message)
