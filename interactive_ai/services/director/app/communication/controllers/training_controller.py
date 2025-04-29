# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the TrainingController"""

import logging
import os

from communication.data_validator import TrainingRestValidator
from communication.exceptions import (
    JobInsufficientBalanceException,
    NotEnoughDatasetItemsException,
    NotEnoughSpaceHTTPException,
    NotReadyForTrainingException,
    ObsoleteTrainingAlgorithmException,
)
from communication.jobs_client import JobsClient
from communication.views.job_rest_views import JobRestViews
from coordination.dataset_manager.missing_annotations_helper import MissingAnnotationsHelper
from entities import TaskTrainReadiness, TrainingConfig
from features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from service.job_submission import ModelTrainingJobSubmitter
from service.label_schema_service import LabelSchemaService
from service.project_service import ProjectService

from geti_fastapi_tools.exceptions import BadRequestException
from geti_telemetry_tools import unified_tracing
from geti_types import ID, DatasetStorageIdentifier
from grpc_interfaces.job_submission.client import InsufficientBalanceException
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.annotation_scene_state import AnnotationState
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, DatasetRepo, LabelSchemaRepo
from sc_sdk.repos.dataset_entity_repo import PipelineDatasetRepo
from sc_sdk.services import ModelService
from sc_sdk.utils.filesystem import check_free_space_for_operation

logger = logging.getLogger(__name__)

# Ratio of dataset items that must be present compared to number of annotations before training can be started
DATASET_ITEM_TO_ANNOTATION_RATIO = float(os.getenv("DATASET_ITEM_TO_ANNOTATION_RATIO", "0.9"))


class TrainingController:
    """
    Control logic for training endpoints.
    """

    @staticmethod
    @unified_tracing
    def train_task(project_id: ID, author: ID, raw_train_config: dict) -> dict:
        """
        Train one task after validating the request and ensuring that the server is ready to train a model.

        :param project_id: ID of the project containing the task to train
        :param author: ID of the user submitting the job
        :param raw_train_config: training configuration for the task
        :return: REST view of the submitted job
        """
        # Validate the request payload against the schema
        TrainingRestValidator().validate_train_request(raw_train_config)

        # Validate the 'task_id'
        project = ProjectService.get_by_id(project_id=project_id)
        task_id_str = raw_train_config.get("task_id")
        if task_id_str:
            # The 'task_id', if provided, must exist in the project
            if project.get_trainable_task_node_by_id(task_id=ID(task_id_str)) is None:
                raise BadRequestException(f"Task with ID `{task_id_str}` does not exist in project `{project_id}`")
        elif len(project.get_trainable_task_nodes()) > 1:
            # The 'task_id' is mandatory for task-chain projects
            raise BadRequestException("Field `task_id` is mandatory for projects with multiple tasks")

        # Ensure the platform has enough storage space to store the training artifacts
        check_free_space_for_operation(operation="Training", exception_type=NotEnoughSpaceHTTPException)

        # Parse the training configuration, filling the blanks with default values
        train_config = TrainingConfig.generate_training_config(
            project=project,
            train_config_dict=raw_train_config if raw_train_config else {},
        )

        # Validate that the model template is not obsolete
        if train_config.model_template_id in ModelTemplateList().obsolete_model_template_ids:
            raise ObsoleteTrainingAlgorithmException(model_template_id=train_config.model_template_id)

        # Check if the task has enough annotations for manual training
        task_ready, reason = TrainingController._is_task_ready_for_manual_training(
            task_train_config=train_config, project=project
        )
        if not task_ready:
            raise NotReadyForTrainingException(reason=reason)

        # If the training costs credits, block premature training requests when the backend still has many
        # new annotations to process, to avoid charging the user for a model trained on limited data.
        if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_CREDIT_SYSTEM):
            annotations_for_train_job, dataset_items_for_train_job = (
                TrainingController.get_annotations_and_dataset_items(
                    project=project, task_node_id=train_config.task.id_
                )
            )
            if dataset_items_for_train_job < (annotations_for_train_job * DATASET_ITEM_TO_ANNOTATION_RATIO):
                raise NotEnoughDatasetItemsException
            if train_config.max_training_dataset_size is None:
                train_config.max_training_dataset_size = dataset_items_for_train_job

        # Submit the job to the scheduler
        train_job_id = TrainingController._submit_train_job(
            project=project, task_training_config=train_config, author=author
        )

        return JobRestViews.job_id_to_rest(job_id=train_job_id)

    @staticmethod
    def get_annotations_and_dataset_items(project: Project, task_node_id: ID) -> tuple[int, int]:
        """
        Get the available number of annotations and dataset items for the task in the training config

        :param project: Project for which the training was started
        :param task_node_id: task node id of the task that will be trained
        :return: Tuple with integers representing the number of annotations and dataset items for the task to train
        """

        training_ds_storage = project.get_training_dataset_storage()
        pipeline_dataset = PipelineDatasetRepo.get_or_create(training_ds_storage.identifier)
        task_dataset_entity = pipeline_dataset.task_datasets[task_node_id]
        is_first_task = project.get_trainable_task_nodes()[0].id_ == task_dataset_entity.task_node_id
        if is_first_task:
            num_annotations = AnnotationSceneStateRepo(training_ds_storage.identifier).count_images_state_for_task(
                annotation_states=[
                    AnnotationState.ANNOTATED,
                    AnnotationState.PARTIALLY_ANNOTATED,
                ],
                task_id=task_dataset_entity.task_node_id,
            )
            num_annotations += AnnotationSceneStateRepo(
                training_ds_storage.identifier
            ).count_video_frames_state_for_task(
                annotation_states=[
                    AnnotationState.ANNOTATED,
                    AnnotationState.PARTIALLY_ANNOTATED,
                ],
                task_id=task_dataset_entity.task_node_id,
            )
        else:
            # Get the non-empty label of the first task
            label_schema = LabelSchemaRepo(project.identifier).get_latest_view_by_task(task_dataset_entity.task_node_id)
            # There can only be one non-empty label for the first task
            label = label_schema.get_labels(include_empty=False)[0]
            _, label_occurrence = AnnotationSceneRepo(training_ds_storage.identifier).count_label_occurrence(
                [label.id_]
            )
            num_annotations = label_occurrence.get(label.id_, 0)

        num_dataset_items = len(DatasetRepo(training_ds_storage.identifier).get_by_id(task_dataset_entity.dataset_id))
        return num_annotations, num_dataset_items

    @staticmethod
    @unified_tracing
    def _submit_train_job(project: Project, task_training_config: TrainingConfig, author: ID) -> ID:
        """
        Submit a training job for the task in the given configuration,
        provided that it meets the manual training annotation requirement and
        the configuration is valid.

        If a task does not already have a model storage for the template specified in
        the respective configuration, then the model storage will be created.

        :param project: Project containing the tasks to train
        :param task_training_config: Configuration defining the parameters to use for
        training the respective task
        :param author: ID of the user submitting the job
        :return: ID of the training job
        """
        task_node = task_training_config.task
        model_storage = ModelService.get_or_create_model_storage(
            project_identifier=project.identifier,
            task_node=task_node,
            model_template_id=task_training_config.model_template_id,
        )

        logger.info("Submitting train job for task with ID `%s`", task_node.id_)
        job_submitter = ModelTrainingJobSubmitter(JobsClient().jobs_client)
        try:
            return job_submitter.execute(
                project=project,
                task_node=task_node,
                model_storage=model_storage,
                from_scratch=task_training_config.train_from_scratch,
                activate_model_storage=True,
                hyper_parameters_id=(
                    task_training_config.hyper_parameters.id_
                    if task_training_config.hyper_parameters and not task_training_config.hyper_parameters.ephemeral
                    else None
                ),
                author=author,
                max_training_dataset_size=task_training_config.max_training_dataset_size,
                reshuffle_subsets=task_training_config.reshuffle_subsets,
            )
        except InsufficientBalanceException:
            logger.error("Insufficient balance for job execution")
            raise JobInsufficientBalanceException("Insufficient balance for job execution")

    @staticmethod
    def _get_task_readiness_status_by_project(project: Project) -> list[TaskTrainReadiness]:
        """
        Returns the TaskTrainReadiness statuses for all tasks in the project. These statuses
        can be used to determine whether a task is ready to accept a manual training trigger or not.

        :param project: Project for which to get the statuses
        :return: List of TaskTrainReadiness statuses for all trainable tasks in the
            project. The statuses are returned in the task order defined in the
            projects TaskGraph.
        """
        training_dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=project.training_dataset_storage_id,
        )
        ordered_tasks = [task for task in project.task_graph.ordered_tasks if task.task_properties.is_trainable]
        task_statuses: list[TaskTrainReadiness] = []
        for _, task in enumerate(ordered_tasks):
            missing_annotations_for_task = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=training_dataset_storage_identifier,
                task_node=task,
            )
            # Label constraint for manual training is only applicable for anomaly tasks
            missing_annotations_per_label = (
                missing_annotations_for_task.missing_annotations_per_label if task.task_properties.is_anomaly else {}
            )
            task_status = TaskTrainReadiness(
                task_id=task.id_,
                total_missing_annotations=missing_annotations_for_task.total_missing_annotations_manual_training,
                missing_annotations_per_label=missing_annotations_per_label,
            )
            task_statuses.append(task_status)
        return task_statuses

    @staticmethod
    def _is_task_ready_for_manual_training(task_train_config: TrainingConfig, project: Project) -> tuple[bool, str]:
        """
        Check if the task specified in the training configurations is ready for manual training.

        Manual training has different conditions than auto training.
        A task is ready for manual training if it requires no additional annotations.
        The minimum number of annotations for manual training is currently 3

        :param task_train_config: TrainingConfig to run the training
        :param project: Project to determine readiness for manual training
        :return: bool indicating whether the project is ready for manual training,
            and string containing a more detailed explanation in case it is not
        """
        ready_for_training = True
        reason = ""

        task_readiness_statuses = TrainingController._get_task_readiness_status_by_project(project)

        task = task_train_config.task
        task_status = next(status for status in task_readiness_statuses if status.task_id == task.id_)
        if not task_status.is_ready:
            ready_for_training = False
            reason = TrainingController._generate_not_ready_message(
                project=project,
                task_status=task_status,
                task=task,
            )
        return ready_for_training, reason

    @staticmethod
    def _generate_not_ready_message(
        project: Project,
        task_status: TaskTrainReadiness,
        task: TaskNode,
    ) -> str:
        """
        Generates a message to display to the user to help them understand why training couldn't be started. Possible
        reasons training can't be started are:
         - More annotations are required (total or per-label)

        :param project: Project containing the task node
        :param task_status: TaskTrainReadiness that contains information on why the task can't be trained
        :param task: The TaskNode that can't be trained
        :return: String message to send to the user
        """
        if not any(task_status.missing_annotations_per_label.values()):
            # There are additional annotations required, but there are no label restrictions.
            reason = (
                f"'{task.title}' is not ready for training, "
                f"{task_status.total_missing_annotations} additional "
                f"annotations are required before training can be "
                f"started."
            )
        else:
            # There are additional annotations required for specific labels
            task_labels = LabelSchemaService.get_latest_labels_for_task(
                project_identifier=project.identifier, task_node_id=task.id_, include_empty=True
            )
            missing_per_label_string = ""
            for (
                label_id,
                missing_annotations,
            ) in task_status.missing_annotations_per_label.items():
                if missing_annotations > 0:
                    label_name = next(label.name for label in task_labels if label.id_ == label_id)
                    missing_per_label_string += f"{label_name}: {missing_annotations}, "
            reason = (
                f"'{task.title}' is not ready for training. There are more "
                f"annotations required for some labels before training can be started. "
                f"The following labels require more annotations: "
                f"{missing_per_label_string[:-2]}."
            )
        return reason
