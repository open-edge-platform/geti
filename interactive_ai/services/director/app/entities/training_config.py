# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from dataclasses import dataclass
from typing import Any

from communication.data_validator import ConfigurationRestValidator
from communication.exceptions import InvalidConfigurationException, TaskNotFoundException, TaskNotTrainableException
from communication.views.configuration_rest_views import ConfigurationRESTViews
from configuration import ConfigurationValidator

from geti_fastapi_tools.exceptions import BadRequestException, BodyMissingRequiredParameters
from geti_telemetry_tools import unified_tracing
from geti_types import ID
from iai_core.configuration.elements.hyper_parameters import HyperParameters
from iai_core.entities.project import Project
from iai_core.entities.task_node import TaskNode
from iai_core.repos import ConfigurableParametersRepo
from iai_core.services import ModelService


@dataclass
class TrainingConfig:
    """
    Store the body of a train rest message as an object.
    """

    model_template_id: str
    task: TaskNode
    train_from_scratch: bool
    reshuffle_subsets: bool = False
    max_training_dataset_size: int | None = None
    hyper_parameters: HyperParameters | None = None

    @classmethod
    @unified_tracing
    def generate_training_config(cls, project: Project, train_config_dict: dict) -> "TrainingConfig":
        """
        Generate a TrainingConfig object from a dictionary, and make sure that the config is valid

        :param project: Project to which the TrainingConfig applies
        :param train_config_dict: Dictionary containing the training configuration
        :return: TrainingConfig corresponding to `train_config_dict`
        """
        task_id = train_config_dict.get("task_id")
        model_template_id = train_config_dict.get("model_template_id")

        if task_id is not None:
            task_id_ = ID(task_id)
            task = project.get_trainable_task_node_by_id(task_id=task_id)
            if not task:
                raise TaskNotFoundException(task_id=task_id)
            if not task.task_properties.is_trainable:
                raise TaskNotTrainableException(task_node=task)
        else:
            trainable_tasks = project.get_trainable_task_nodes()
            if len(trainable_tasks) > 1:
                raise BodyMissingRequiredParameters(
                    "The 'train_config_dict' must contain a 'task_id' for task-chain projects."
                )
            task = trainable_tasks[0]
            task_id_ = task.id_

        if model_template_id is None:
            model_template_id = TrainingConfig._get_active_model_template_id_for_task(project=project, task_id=task_id_)

        train_from_scratch = train_config_dict.get("train_from_scratch", False)

        reshuffle_subsets = train_config_dict.get("reshuffle_subsets", False)

        # Reshuffling of subsets can be enabled only if training from scratch
        if reshuffle_subsets and not train_from_scratch:
            raise BadRequestException("Reshuffling of subsets can be enabled only when training from scratch!")

        hyper_parameters = train_config_dict.get("hyper_parameters")

        if hyper_parameters is not None:
            hyper_parameters = TrainingConfig._create_and_validate_hyper_parameters(
                project=project, task=task, hyper_parameters=hyper_parameters
            )
            # Mark the hyper-parameters as 'single-use' to limit their scope to this
            # training job only, then save them in the DB so the job can retrieve them
            hyper_parameters.single_use = True
            ConfigurableParametersRepo(project.identifier).save(hyper_parameters)

        dataset_size = train_config_dict.get("max_training_dataset_size")
        return cls(
            task=task,
            model_template_id=model_template_id,
            train_from_scratch=train_from_scratch,
            reshuffle_subsets=reshuffle_subsets,
            max_training_dataset_size=dataset_size,
            hyper_parameters=hyper_parameters,
        )

    @classmethod
    @unified_tracing
    def generate_default_training_configs(cls, project: Project) -> list["TrainingConfig"]:
        """
        Generate training configs to train all tasks in the project with either their
        active model architecture or the default model architecture for the task.

        :param project: Project to generate the training configs for
        :return: List of TrainingConfigs, one for each trainable task in the project
        """
        tasks = project.get_trainable_task_nodes()
        training_configs: list[TrainingConfig] = []
        for task in tasks:
            model_template_id = TrainingConfig._get_active_model_template_id_for_task(project=project, task_id=task.id_)
            training_configs.append(
                cls(
                    model_template_id=model_template_id,
                    task=task,
                    train_from_scratch=False,
                    reshuffle_subsets=False,
                )
            )
        return training_configs

    @staticmethod
    def _create_and_validate_hyper_parameters(
        project: Project, task: TaskNode, hyper_parameters: dict[str, Any]
    ) -> HyperParameters:
        """
        Extract and validate the hyper parameters for a training round from a
        `hyper_parameters` dictionary

        :param project: Project to which the hyper parameters apply
        :param task: Task for which the hyper parameters should be validated
        :return: HyperParameters instance, containing the validated hyper parameters
        """
        ConfigurationRestValidator().validate_task_configuration(hyper_parameters)
        (
            input_config,
            entity_identifier,
        ) = ConfigurationRESTViews.config_list_from_rest_dict(
            rest_input=hyper_parameters,
            workspace_id=project.workspace_id,
            project_id=project.id_,
            task_id=task.id_,
        )[0]
        valid_hyper_parameters = ConfigurationValidator.validate_and_update_config(
            input_config=input_config,
            entity_identifier=entity_identifier,
            project=project,
            task_id=task.id_,
        )
        if not isinstance(valid_hyper_parameters, HyperParameters):
            raise InvalidConfigurationException(
                f"Training configuration contained invalid hyper parameters of "
                f"type {type(valid_hyper_parameters)}, unable to start training."
            )
        return valid_hyper_parameters

    @staticmethod
    def _get_active_model_template_id_for_task(project: Project, task_id: ID) -> str:
        """
        Get the model_template_id of the active model (or the default model, if no
        model has been trained yet) for a task.

        :param project: Project in which the task lives
        :param task_id: ID of the Task to get the active model_template_id for
        """
        active_model_storage = ModelService.get_active_model_storage(
            project_identifier=project.identifier,
            task_node_id=task_id,
        )
        return active_model_storage.model_template.model_template_id
