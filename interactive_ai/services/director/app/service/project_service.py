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

"""
This module contains the ProjectService class
"""

import logging
from functools import lru_cache

from communication.exceptions import DatasetStorageNotInProjectException
from configuration import ComponentRegisterEntry, ConfigurableComponentRegister
from storage.repos import DatasetItemCountRepo, DatasetItemLabelsRepo
from storage.repos.auto_train_activation_repo import ProjectBasedAutoTrainActivationRepo

from geti_fastapi_tools.exceptions import ProjectNotFoundException
from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from sc_sdk.entities.project import NullProject, Project
from sc_sdk.repos import ConfigurableParametersRepo, ProjectRepo

logger = logging.getLogger(__name__)


class ProjectService:
    @staticmethod
    def get_by_id(project_id: ID) -> Project:
        """
        Get a project given its ID.

        :param project_id: ID of the project
        :return: Project
        :raises ProjectNotFoundException: if the project does not exist
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        return project

    @staticmethod
    def init_configuration(project_id: ID) -> None:
        """
        This method initializes the configurable parameters for all components and tasks
        in the project. It creates database entries containing the default values for the
        configurable parameters for all components in the project.

        :param project_id: Project to initialize the configurable parameters for
        """
        project = ProjectService.get_by_id(project_id)
        config_repo = ConfigurableParametersRepo(project.identifier)

        for component in ComponentType:
            if component is ComponentType.NULL_COMPONENT:
                continue

            register_data: ComponentRegisterEntry = ConfigurableComponentRegister[component.name].value
            if component.metadata.per_task:
                trainable_tasks = project.get_trainable_task_nodes()
                for task in trainable_tasks:
                    configuration_type = register_data.get_configuration_type(task_type=task.task_properties.task_type)
                    config_repo.get_or_create_component_parameters(
                        data_instance_of=configuration_type,
                        component=component,
                        task_id=task.id_,
                    )
            else:
                config_repo.get_or_create_component_parameters(
                    data_instance_of=register_data.get_configuration_type(),
                    component=component,
                    task_id=None,
                )

    @staticmethod
    def delete_entities(workspace_id: ID, project_id: ID, dataset_storage_id: ID) -> None:
        """
        Deletes entities created by the director microservice.

        Includes:
            - DatasetItemCount
            - DatasetItemLabels
            - AutoTrainActivation

        Warning: deletion may change with: CVS-86033

        :param workspace_id: ID of the workspace the project belongs to
        :param project_id: ID of the project:
        :param dataset_storage_id: ID of the dataset storage
        """
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )

        DatasetItemCountRepo(dataset_storage_identifier=dataset_storage_identifier).delete_all()
        DatasetItemLabelsRepo(dataset_storage_identifier=dataset_storage_identifier).delete_all()
        ProjectBasedAutoTrainActivationRepo(project_identifier=project_identifier).delete_all()

    @staticmethod
    def unlock(job_type: str, project_id: ID) -> None:
        """
        Unlocks a project for modifications.

        :param job_type: The job type that originally locked the project
        :param project_id: The ID of the project to unlock
        """
        lock_owner = job_type
        logger.info("Unlocking project with ID '%s' for lock owner '%s'.", project_id, lock_owner)
        ProjectRepo().mark_unlocked(owner=lock_owner, project_id=project_id)

    @staticmethod
    @lru_cache
    def is_training_dataset_storage_id(project_id: ID, dataset_storage_id: ID) -> bool:
        """
        Return True if the given dataset storage id is an id of the training DS in the project with given id

        :param project_id: ID of project
        :param dataset_storage_id: ID of the dataset storage
        :return: True if given DS ID is training DS in project with given id
        """
        project = ProjectService.get_by_id(project_id)
        return project.training_dataset_storage_id == dataset_storage_id

    @staticmethod
    def get_dataset_storage_by_id(project: Project, dataset_storage_id: ID) -> DatasetStorage:
        """
        Get dataset storage in project if dataset storage with given id exists in project

        :param project: project to get DS from
        :param dataset_storage_id: id of dataset storage entity
        :return: instance of DatasetStorage
        :raises: DatasetStorageNotInProjectException if the storage does not belong to the project
        """
        dataset_storage = project.get_dataset_storage_by_id(dataset_storage_id)
        if isinstance(dataset_storage, NullDatasetStorage):
            raise DatasetStorageNotInProjectException(project=project, dataset_storage_id=dataset_storage_id)
        return dataset_storage
