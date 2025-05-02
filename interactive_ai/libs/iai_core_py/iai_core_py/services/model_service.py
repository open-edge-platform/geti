# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the ModelService class responsible for handling common
usecases related to the active model, like obtaining the active model or active model
storage and updating the active model storage.
"""

import logging
import os

from iai_core_py.adapters.model_adapter import DataSource
from iai_core_py.algorithms import ModelTemplateList
from iai_core_py.entities.active_model_state import ActiveModelState, NullActiveModelState
from iai_core_py.entities.model import Model, ModelPurgeInfo, NullModel
from iai_core_py.entities.model_storage import ModelStorage, ModelStorageIdentifier
from iai_core_py.entities.model_template import NullModelTemplate
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.repos import ActiveModelStateRepo, ModelRepo, ModelStorageRepo
from iai_core_py.repos.model_repo import ModelStatusFilter
from iai_core_py.utils.exceptions import (
    PurgeActiveModelException,
    PurgeLatestModelException,
    PurgeOptimizedModelException,
    SDKModelNotFoundException,
)
from iai_core_py.utils.time_utils import now

from geti_types import ID, ProjectIdentifier

logger = logging.getLogger(__name__)

# Amount of models that will keep their binaries in the model storage. If a new model is saved that will exceed this
# number, the oldest model will have its binaries purged.
NUM_MODELS_TO_KEEP_IN_STORAGE = int(os.getenv("NUM_MODELS_TO_KEEP_IN_STORAGE", "20"))

logger.info(f"Auto model archival configured to keep {NUM_MODELS_TO_KEEP_IN_STORAGE} models in storage.")


class ModelService:
    """
    ModelService handles common usecases related to the model.
    """

    @staticmethod
    def get_active_model_storage(
        project_identifier: ProjectIdentifier,
        task_node_id: ID,
    ) -> ModelStorage:
        """
        Get active model storage for a task node.

        :param project_identifier: Identifier of the project containing the task node
        :param task_node_id: ID of the task node
        :return: ModelStorage that is currently active for the task node
        """
        active_model_state = ModelService._get_active_model_state(
            project_identifier=project_identifier, task_node_id=task_node_id
        )
        return active_model_state.active_model_storage

    @staticmethod
    def get_base_active_model(project_identifier: ProjectIdentifier, task_node_id: ID) -> Model:
        """
        Get the base active model (base-framework, non-optimized) for a task node.

        The active model is the latest improved base-framework model in the active
        model storage of a task node.

        :param project_identifier: Identifier of the project containing the model
        :param task_node_id: ID of the task node associated with the model
        :return: Inference model that is currently active for the task node
        """
        model_storage = ModelService.get_active_model_storage(
            project_identifier=project_identifier,
            task_node_id=task_node_id,
        )

        return ModelRepo(model_storage.identifier).get_latest(
            model_status_filter=ModelStatusFilter.IMPROVED, include_optimized_models=False
        )

    @staticmethod
    def get_inference_active_model(project_identifier: ProjectIdentifier, task_node_id: ID) -> Model:
        """
        Get inference active model for a task node, i.e. OpenVINO MO model.

        The active model is the latest improved base-framework model in the active
        model storage of a task node.

        :param project_identifier: Identifier of the project containing the model
        :param task_node_id: ID of the task node associated with the model
        :return: Inference model that is currently active for the task node
        """
        model_storage = ModelService.get_active_model_storage(
            project_identifier=project_identifier,
            task_node_id=task_node_id,
        )

        return ModelRepo(model_storage.identifier).get_latest_model_for_inference()

    @staticmethod
    def get_inference_active_model_id(project_identifier: ProjectIdentifier, task_node_id: ID) -> ID:
        """
        Get the id of the inference active model for a task node, i.e. OpenVINO MO model.

        The active model is the latest improved base-framework model in the active
        model storage of a task node.

        :param project_identifier: Identifier of the project containing the model
        :param task_node_id: ID of the task node associated with the model
        :return: ID of the inference model that is currently active for the task node
        """
        model_storage = ModelService.get_active_model_storage(
            project_identifier=project_identifier,
            task_node_id=task_node_id,
        )

        return ModelRepo(model_storage.identifier).get_latest_model_id_for_inference()

    @staticmethod
    def activate_model_storage(model_storage: ModelStorage) -> None:
        """
        Activate a model storage for its relative task node.

        :param model_storage: ModelStorage to activate
        """
        # Get the current active model state
        project_identifier = model_storage.project_identifier
        task_node_id = model_storage.task_node_id
        active_model_state = ModelService._get_active_model_state(
            project_identifier=project_identifier,
            task_node_id=task_node_id,
        )
        # Set the new model storage as active
        active_model_state.active_model_storage = model_storage
        logger.info(
            "Updating active model state of task node with id %s to model storage with id %s.",
            task_node_id,
            model_storage.id_,
        )
        # Save changes to repo
        ActiveModelStateRepo(project_identifier).save(active_model_state)

    @staticmethod
    def is_model_storage_activable(model_storage: ModelStorage) -> bool:
        """
        Return whether the model storage can be activated. A model storage can be
        activated only if it contains a model with ModelStatus [SUCCESS].

        :param model_storage: the model storage to check
        :return: True if activable, False otherwise.
        """
        model_repo = ModelRepo(model_storage.identifier)
        return model_repo.get_latest_successful_version() != 0

    @staticmethod
    def _get_active_model_state(
        project_identifier: ProjectIdentifier,
        task_node_id: ID,
    ) -> ActiveModelState:
        """
        Get the active model state of the given task node

        :param project_identifier: Identifier of the project containing the task node
        :param task_node_id: ID of the task node relative to the active model
        :return: ActiveModelState of the task node
        :raises: ValueError if the task node id is invalid
        """
        active_model_state_repo = ActiveModelStateRepo(project_identifier)
        active_model_state = active_model_state_repo.get_by_task_node_id(task_node_id)
        if isinstance(active_model_state, NullActiveModelState):
            raise ValueError(f"ActiveModelState with task node id {task_node_id} does not exist.")
        return active_model_state

    @staticmethod
    def get_or_create_model_storage(
        project_identifier: ProjectIdentifier,
        task_node: TaskNode,
        model_template_id: str,
    ) -> ModelStorage:
        """
        Returns the model storage for a particular task_node and model_template. If no
        model storage for that task node and model template exists, this method will
        create one.

        :param project_identifier: Identifier of the project containing the task node
        :param task_node: Task node associated with the model storage to get
        :param model_template_id: Identifier of the model template associated with
            the model storage to get
        :return: ModelStorage
        """
        model_storage: ModelStorage | None = None
        model_storage_repo = ModelStorageRepo(project_identifier)
        model_storages = model_storage_repo.get_by_task_node_id(task_node_id=task_node.id_)

        for task_model_storage in model_storages:
            if task_model_storage.model_template.model_template_id == model_template_id:
                model_storage = task_model_storage
        if model_storage is None:
            model_template = ModelTemplateList().get_by_id(model_template_id)
            if (
                isinstance(model_template, NullModelTemplate)
                or model_template.task_type != task_node.task_properties.task_type
            ):
                available_algos = [
                    model_template.model_template_id
                    for model_template in ModelTemplateList().get_all()
                    if model_template.task_type == task_node.task_properties.task_type
                ]
                raise ValueError(
                    f"Algorithm with name '{model_template_id}' was not found for task "
                    f"{task_node.title} of type {task_node.task_properties.task_type}. "
                    f"Algorithms that are available to this task are: {available_algos}."
                )
            model_storage = ModelStorage(
                id_=ModelStorageRepo.generate_id(),
                project_id=project_identifier.project_id,
                task_node_id=task_node.id_,
                model_template=model_template,
            )
            model_storage_repo.save(model_storage)
        return model_storage

    @staticmethod
    def purge_model_binaries(workspace_id: ID, project_id: ID, model_storage_id: ID, model_id: ID, user_id: ID) -> None:
        """
        Purges the binaries of a model and its optimized models and saves the updated models in a purged state. This
        entails model weights, linked optimized model weights and exportable code. Only allowed on base models which are
        not the active model or the latest model.

        :param workspace_id: ID of the workspace containing the model.
        :param project_id: ID of the project containing the model.
        :param model_storage_id: ID of the model storage containing the model to purge.
        :param model_id: ID of the model to purge
        :param user_id: ID of the user that requested to purge the model
        """
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=workspace_id, project_id=project_id, model_storage_id=model_storage_id
        )
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
        model_storage = ModelStorageRepo(project_identifier).get_by_id(model_storage_id)
        model = ModelRepo(model_storage_identifier).get_by_id(model_id)

        if isinstance(model, NullModel):
            raise SDKModelNotFoundException(model_id)

        # Validate model can be purged
        if model.purge_info.is_purged:
            return
        if model.is_optimized():
            raise PurgeOptimizedModelException
        if (
            ModelService.get_base_active_model(
                project_identifier=project_identifier, task_node_id=model_storage.task_node_id
            )
            == model
        ):
            raise PurgeActiveModelException
        latest_model_version = ModelRepo(model_storage_identifier).get_latest_successful_version()
        if model.version == latest_model_version:
            raise PurgeLatestModelException

        optimized_models = ModelRepo(model_storage_identifier).get_optimized_models_by_base_model_id(model_id)
        models = [model, *optimized_models]

        # First save all models as purged. This is done to ensure in case of an error during deletion the faulty models
        # will be excluded from find methods in the repo.
        purge_info = ModelPurgeInfo(is_purged=True, purge_time=now(), user_uid=user_id)
        for model in models:
            model.purge_info = purge_info
            model.size = 0
            ModelRepo(model_storage_identifier).set_purge_info(model)

        # Cleanup binaries for models and unset all items related to the binaries
        ModelService._cleanup_model_binaries(
            model_storage_identifier=model_storage_identifier, models=models, purge_info=purge_info
        )

    @staticmethod
    def _cleanup_model_binaries(
        model_storage_identifier: ModelStorageIdentifier, models: list[Model], purge_info: ModelPurgeInfo
    ) -> None:
        binary_repo = ModelRepo(model_storage_identifier).binary_repo
        for model in models:
            for key, value in model.weight_paths.items():
                binary_repo.delete_by_filename(value)
                model.delete_data(key)
            if model.exportable_code_adapter is not None and isinstance(
                model.exportable_code_adapter.data_source, DataSource
            ):
                binary_repo.delete_by_filename(model.exportable_code_adapter.data_source.binary_filename)
                model.exportable_code = None
            model.purge_info = purge_info
            ModelRepo(model_storage_identifier).save(model)

    @staticmethod
    def get_model_size(model: Model, model_storage_identifier: ModelStorageIdentifier) -> int:
        """
        Get the size of the model in bytes. Includes base model weights, optimized model weights and exportable code.
        If this is called on an optimized model it only includes the size of the optimized models' weights.

        :param model: Model to get the size for
        :param model_storage_identifier: Model storage identifier
        :return: Size of the model and any items related to the model in bytes
        """
        if model.is_optimized():
            return model.size

        if model.purge_info.is_purged:
            return 0

        size = 0
        binary_repo = ModelRepo(model_storage_identifier).binary_repo
        optimized_models = ModelRepo(model_storage_identifier).get_optimized_models_by_base_model_id(model.id_)
        models = [model, *optimized_models]
        for model in models:  # noqa: PLR1704
            for key, value in model.weight_paths.items():
                # Skip checking very small files such as the label schema.
                if not value.endswith(".xml") and not value.endswith(".json"):
                    size += binary_repo.get_object_size(value)
            if model.exportable_code_adapter is not None:
                size += binary_repo.get_object_size(model.exportable_code_adapter.data_source.binary_filename)  # type: ignore[union-attr]
        return size

    @staticmethod
    def auto_archive_models(identifier: ModelStorageIdentifier) -> None:
        """
        Checks the model storage for the maximum amount of base models that can be saved in it. If the current saved
        amount is equal or higher than the currently set value for the model storage, purge the oldest models binaries.

        :param identifier: ModelStorageIdentifier to check saved models for.
        """
        if NUM_MODELS_TO_KEEP_IN_STORAGE > 0:
            non_purged_base_models = ModelRepo(identifier).get_non_purged_base_models()
            for model in non_purged_base_models[:-NUM_MODELS_TO_KEEP_IN_STORAGE]:
                ModelService.purge_model_binaries(
                    workspace_id=identifier.workspace_id,
                    project_id=identifier.project_id,
                    model_storage_id=identifier.model_storage_id,
                    model_id=model.id_,
                    user_id=ID(),
                )

    @staticmethod
    def save_with_auto_archival(model: Model, identifier: ModelStorageIdentifier) -> None:
        """
        Saves the models and then auto archives models if necessary.

        :param model: Model to save
        :param identifier: ModelStorageIdentifier to save the model to the correct ModelStorage
        """
        ModelRepo(identifier).save(model)
        if not model.is_optimized():
            ModelService.auto_archive_models(identifier)
