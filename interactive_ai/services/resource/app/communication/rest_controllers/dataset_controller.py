# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Any

from communication.constants import MAX_NUMBER_OF_DATASET_STORAGES
from communication.exceptions import (
    DatasetStorageAlreadyExistsException,
    DatasetStorageNotInProjectException,
    MaxNumberOfDatasetsException,
    TrainingRevisionNotFoundException,
)
from communication.rest_data_validator import DatasetRestValidator
from communication.rest_views.dataset_storage_rest_views import NAME, DatasetStorageRESTViews
from managers.project_manager import ProjectManager
from usecases.statistics import StatisticsUseCase

from geti_fastapi_tools.exceptions import BadRequestException, DatasetStorageNotFoundException
from geti_fastapi_tools.responses import success_response_rest
from geti_telemetry_tools import unified_tracing
from geti_types import ID, DatasetStorageIdentifier, Singleton
from iai_core_py.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from iai_core_py.entities.datasets import NullDataset
from iai_core_py.repos import DatasetRepo, DatasetStorageRepo, ProjectRepo
from iai_core_py.utils.deletion_helpers import DeletionHelpers


class DatasetRESTController(metaclass=Singleton):
    @staticmethod
    def create_dataset_storage(project_id: ID, data: dict) -> dict[str, Any]:
        """
        Create new dataset storage and assign it to project with given id

        :param project_id: id of project to add DS to
        :param data: dataset storage creation data
        :return: created dataset storage REST representation
        :raises: ValidationError if the data does not comply with the JSON schema
        :raises: DatasetStorageAlreadyExistsException if DS with given name already exists
        """
        DatasetRestValidator().validate_creation_data(data)
        name = data.get(NAME)
        if name is None:
            raise BadRequestException("Dataset creation requires providing a name in the request body.")
        project = ProjectManager.get_project_by_id(project_id)
        if MAX_NUMBER_OF_DATASET_STORAGES and project.dataset_storage_count >= MAX_NUMBER_OF_DATASET_STORAGES:
            raise MaxNumberOfDatasetsException(MAX_NUMBER_OF_DATASET_STORAGES)
        if name in {ds.name for ds in project.get_dataset_storages()}:
            raise DatasetStorageAlreadyExistsException(name)
        dataset_storage = DatasetStorage(
            _id=DatasetStorageRepo.generate_id(),
            name=name,
            project_id=project_id,
            use_for_training=False,
        )
        ProjectManager.add_dataset_storage(project, dataset_storage)
        return DatasetStorageRESTViews.dataset_storage_to_rest(dataset_storage)

    @staticmethod
    def get_dataset_storages(project_id: ID) -> dict[str, Any]:
        """
        Get all dataset storages in project with id

        :param project_id: ID of project
        :return: dataset storages in project in REST representation
        """
        project = ProjectManager.get_project_by_id(project_id)
        dataset_storages = project.get_dataset_storages()
        return DatasetStorageRESTViews.dataset_storages_to_rest(dataset_storages)

    @staticmethod
    def get_dataset_storage(project_id: ID, dataset_storage_id: ID) -> dict[str, Any]:
        """
        Get  dataset storage in project  with id

        :param project_id: ID of project
        :param dataset_storage_id: ID of dataset storage id
        :return: dataset storage REST representation
        """
        project = ProjectManager.get_project_by_id(project_id)
        dataset_storage = ProjectManager.get_dataset_storage_by_id(project, dataset_storage_id)
        return DatasetStorageRESTViews.dataset_storage_to_rest(dataset_storage)

    @staticmethod
    def delete_dataset_storage(project_id: ID, dataset_storage_id: ID) -> dict[str, Any]:
        """
        remove dataset storage from list of DSs in project
        then delete DS along with child entities in db

        :param project_id: id of project using DS
        :param dataset_storage_id: id of DS to delete
        :return: success response
        """
        project = ProjectManager.get_project_by_id(project_id)
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage_id,
        )

        adapter_to_delete = next(
            (adapter for adapter in project.dataset_storage_adapters if adapter.id_ == dataset_storage_id),
            None,
        )
        if adapter_to_delete is None:
            raise DatasetStorageNotInProjectException(project=project, dataset_storage_id=dataset_storage_id)

        dataset_storage = adapter_to_delete.get()
        if dataset_storage.use_for_training:
            raise BadRequestException("The main dataset, used for training, cannot be deleted.")

        project.dataset_storage_adapters.remove(adapter_to_delete)
        ProjectRepo().save(project)

        DeletionHelpers.delete_dataset_storage_by_id(dataset_storage_identifier)
        return success_response_rest()

    @staticmethod
    def update_dataset_storage(project_id: ID, dataset_storage_id: ID, data: dict) -> dict[str, Any]:
        """
        Update dataset storage entity based on given data

        :param project_id: id of project using DS
        :param dataset_storage_id: id of DS to update
        :param data: dict containing new info to update the DS
        :return: updated dataset storage REST representation
        """
        project = ProjectManager.get_project_by_id(project_id)
        dataset_storage = project.get_dataset_storage_by_id(dataset_storage_id)
        if isinstance(dataset_storage, NullDatasetStorage):
            raise DatasetStorageNotInProjectException(project, dataset_storage_id)

        name = data.get("name")
        if name:
            name = str(name)
            if name in {ds.name for ds in project.get_dataset_storages()}:
                raise DatasetStorageAlreadyExistsException(name)
            dataset_storage.name = name

        DatasetStorageRepo(project.identifier).save(dataset_storage)
        return DatasetStorageRESTViews.dataset_storage_to_rest(dataset_storage)

    @staticmethod
    @unified_tracing
    def get_dataset_storage_statistics(project_id: ID, dataset_storage_id: ID) -> dict[str, Any]:
        """
        Gets the dataset statistics on a dataset storage level.

        :param project_id: ID of the project to get statistics for
        :param dataset_storage_id: ID of the dataset storage to get statistics for
        :return: Dataset stats REST view or error response
        """
        project = ProjectManager.get_project_by_id(project_id=project_id)
        dataset_storage = DatasetStorageRepo(project.identifier).get_by_id(dataset_storage_id)
        if isinstance(dataset_storage, NullDatasetStorage):
            raise DatasetStorageNotFoundException(dataset_storage_id)
        return StatisticsUseCase.get_dataset_storage_statistics(project=project, dataset_storage=dataset_storage)

    @staticmethod
    @unified_tracing
    def get_dataset_storage_statistics_for_task(
        project_id: ID,
        dataset_storage_id: ID,
        task_id: ID,
    ) -> dict[str, Any]:
        """
        Gets the dataset storage statistics on a task level.

        :param project_id: ID of the project the task belongs to
        :param dataset_storage_id: ID of the dataset storage to get statistics for
        :param task_id: ID of the task to get stats for
        :return: Task stats REST view or error response
        """
        project = ProjectManager.get_project_by_id(project_id=project_id)
        dataset_storage = DatasetStorageRepo(project.identifier).get_by_id(dataset_storage_id)
        if isinstance(dataset_storage, NullDatasetStorage):
            raise DatasetStorageNotFoundException(dataset_storage_id)
        return StatisticsUseCase.get_dataset_storage_statistics_for_task(
            project=project, dataset_storage=dataset_storage, task_id=task_id
        )

    @staticmethod
    @unified_tracing
    def get_dataset_statistics(
        project_id: ID,
        dataset_storage_id: ID,
        dataset_id: ID,
    ) -> dict[str, Any]:
        """
        Gets the dataset storage statistics on a task level.

        :param project_id: ID of the project the task belongs to
        :param dataset_storage_id: ID of the dataset storage to get statistics for
        :param dataset_id: ID of the dataset to get stats for
        :return: Dataset stats REST view or error response
        """
        project = ProjectManager.get_project_by_id(project_id=project_id)
        dataset_storage = DatasetStorageRepo(project.identifier).get_by_id(dataset_storage_id)
        if isinstance(dataset_storage, NullDatasetStorage):
            raise DatasetStorageNotFoundException(dataset_storage_id)
        dataset = DatasetRepo(dataset_storage.identifier).get_by_id(dataset_id)
        if isinstance(dataset, NullDataset):
            raise TrainingRevisionNotFoundException(dataset_id)
        return StatisticsUseCase.get_dataset_statistics(dataset_storage=dataset_storage, dataset=dataset)
