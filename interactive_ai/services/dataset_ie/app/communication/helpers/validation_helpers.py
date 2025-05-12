# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements validation helpers for dataset IE endpoints
"""

import logging

from bson import ObjectId

from communication.helpers.http_exceptions import BadRequestGetiBaseException
from communication.helpers.import_utils import ImportUtils
from domain.entities.geti_project_type import GetiProjectType

from geti_fastapi_tools.exceptions import DatasetStorageNotFoundException, InvalidIDException, ProjectNotFoundException
from geti_types import ID, ProjectIdentifier
from iai_core.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from iai_core.entities.project import NullProject, Project
from iai_core.repos import DatasetStorageRepo, ProjectRepo

logger = logging.getLogger(__name__)


def get_validated_project_type_from_task_type(task_type: str) -> GetiProjectType:
    """
    Get geti project type from task type

    :param task_type: task type
    :return: GetiProjectType
    """
    project_type = ImportUtils.rest_task_type_to_project_type(rest_task_type=task_type)
    if project_type == GetiProjectType.UNKNOWN:
        error_msg = f"Given task_type is not a supported task type: task_type: {task_type}"
        logger.warning(error_msg)
        raise BadRequestGetiBaseException(error_msg)

    if project_type == GetiProjectType.HIERARCHICAL_CLASSIFICATION:
        project_type = GetiProjectType.CLASSIFICATION
    return project_type


def get_validated_project(project_id: str) -> Project:
    """Validate and returns project from project_id"""
    project_id = get_validated_mongo_id(id=project_id, id_name="project_id")
    project = ProjectRepo().get_by_id(project_id)
    if isinstance(project, NullProject):
        raise ProjectNotFoundException(project_id)
    return project


def get_validated_dataset_storage(identifier: ProjectIdentifier, dataset_storage_id: str) -> DatasetStorage:
    """Validate and returns dataset storage from project identifier and dataset_storage_id"""
    dataset_storage_id = get_validated_mongo_id(id=dataset_storage_id, id_name="dataset_storage_id")
    dataset_storage = DatasetStorageRepo(identifier).get_by_id(dataset_storage_id)
    if isinstance(dataset_storage, NullDatasetStorage):
        raise DatasetStorageNotFoundException(ID(dataset_storage_id))
    return dataset_storage


def get_validated_mongo_id(id: str, id_name: str = "file_id") -> ID:
    """Validate and returns ID from mongo id"""
    if not ObjectId.is_valid(id):
        raise InvalidIDException(id_name=id_name, invalid_id=id)
    return ID(id)
