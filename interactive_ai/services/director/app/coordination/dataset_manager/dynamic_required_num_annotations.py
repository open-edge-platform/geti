# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import logging
from math import ceil, log
from typing import TYPE_CHECKING

from coordination.dataset_manager.dataset_counter_config import (
    AnomalyDatasetCounterConfig,
    ClassificationDatasetCounterConfig,
    DatasetCounterConfig,
    KeypointDetectionCounterConfig,
)

from geti_types import ID, ProjectIdentifier
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.entities.evaluation_result import EvaluationPurpose
from sc_sdk.entities.metrics import NullPerformance, Performance
from sc_sdk.entities.model import NullModel
from sc_sdk.entities.model_template import TaskType
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import ConfigurableParametersRepo, EvaluationResultRepo, ModelRepo, ProjectRepo
from sc_sdk.services.model_service import ModelService

if TYPE_CHECKING:
    from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters


# New number of images is calculated to achieve a relative increase of 10% value from the current performance
PERFORMANCE_INCREASE = 0.1

# Maximum performance used in the calculation of num of images. It can not be 1 to keep log calculations valid.
MAXIMUM_PERFORMANCE = 0.9999

# List of tasks for which dynamic annotations calculation is done on "model_activated" event.
DRA_ELIGIBLE_TASK_TYPES = [
    TaskType.CLASSIFICATION,
    TaskType.DETECTION,
    TaskType.SEGMENTATION,
    TaskType.INSTANCE_SEGMENTATION,
    TaskType.ROTATED_DETECTION,
]

logger = logging.getLogger(__name__)


class DynamicRequiredAnnotations:
    @staticmethod
    def on_model_activated(project_identifier: ProjectIdentifier, task_node_id: ID) -> None:
        """
        Calculates the (minimum) number of images required for auto-training based on the performance history of the
        model and the number of images used. The threshold is calculated to achieve a relative improvement of
        PERFORMANCE_INCREASE from the current performance.

        :param project_identifier: Identifier of the project
        :param task_node_id: Identifier of the task node (which is just trained or activated)
        """
        project = ProjectRepo().get_by_id(project_identifier.project_id)
        task_node = project.get_trainable_task_node_by_id(task_id=task_node_id)
        if task_node is None:
            logger.warning(
                f"A trainable task node with id {task_node_id} not found in project {project_identifier}; Skipping."
            )
            return

        is_eligible_task = task_node.task_properties.task_type in DRA_ELIGIBLE_TASK_TYPES

        if not is_eligible_task:
            logger.info(f"Dynamic required annotations is not supported for {project_identifier}; Skipping.")
            return

        # For each task, calculate and update the dynamic required number of annotations in the respective
        # config param repos
        DynamicRequiredAnnotations._update_dynamic_required_num_annotations(project=project, task_node=task_node)

    @staticmethod
    def _get_model_performance_and_dataset_size(project: Project, task_node: TaskNode) -> tuple[Performance, int]:
        """
        Get the test set accuracy on the last trained model as well as the number of images the model was trained on.
        If there is no performance yet or the model is a NullModel,
        this method will return a NullPerformance.

        :param project: Project entity
        :param task_node: Task node entity
        :return: model score from test evaluation results or NullPerformance, and the size of the dataset used for
        training
        """
        model_storage = ModelService.get_active_model_storage(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
        )

        model_repo = ModelRepo(model_storage.identifier)
        model = model_repo.get_latest(include_optimized_models=False)

        dataset = model.get_train_dataset()
        dataset_size = len(dataset) if dataset is not None else 0

        if isinstance(model, NullModel):
            return NullPerformance(), dataset_size

        logger.info(f"Number of images used for training the model ({model.id_}): {dataset_size}")

        equivalent_model_ids = model_repo.get_all_equivalent_model_ids(model)

        return (
            EvaluationResultRepo(project.identifier).get_performance_by_model_ids(
                equivalent_model_ids, purpose=EvaluationPurpose.TEST
            ),
            dataset_size,
        )

    @staticmethod
    def _update_dynamic_required_num_annotations(project: Project, task_node: TaskNode) -> None:
        """
        Calculate the dynamic required number of annotations for the given task node based on the model performance
        history and the number of images used for training till now.
        Update the required_images_auto_training_dynamic field in the ComponentParameters config for the task node.

        :param project: Project entity
        :param task_node: Task node entity
        """

        # Get the config repo and the ComponentParameters config for the task node
        config_type: type[ConfigurableParameters]
        if task_node.task_properties.is_anomaly:
            config_type = AnomalyDatasetCounterConfig
        elif task_node.task_properties.task_type == TaskType.CLASSIFICATION:
            config_type = ClassificationDatasetCounterConfig
        elif task_node.task_properties.task_type == TaskType.KEYPOINT_DETECTION:
            config_type = KeypointDetectionCounterConfig
        else:
            config_type = DatasetCounterConfig

        config_param_repo = ConfigurableParametersRepo(project.identifier)
        config = config_param_repo.get_or_create_component_parameters(
            data_instance_of=config_type,
            component=ComponentType.DATASET_COUNTER,
            task_id=task_node.id_,
        )

        model_performance, assigned_items_count = DynamicRequiredAnnotations._get_model_performance_and_dataset_size(
            project=project, task_node=task_node
        )

        if isinstance(model_performance, NullPerformance):
            logger.info(
                f"Couldn't fetch the  model performance! "
                f"Skipping dynamic annotations calculation for task node {task_node.id_} "
            )
            return
        if assigned_items_count == 0:
            logger.info(
                f"Skipping dynamic annotations calculation for task node {task_node.id_} because no images "
                f"have been used for training."
            )
            return

        model_performance_score = model_performance.score.value

        if model_performance_score == 0.0:
            logger.info(
                f"Skipping dynamic annotations calculation for task node {task_node.id_} because model "
                f"performance is 0."
            )
            return

        if model_performance_score >= MAXIMUM_PERFORMANCE:
            # If the model has already achieved maximum performance, then make the required_images to be dataset size
            required_images = assigned_items_count
            logging.info(
                f"Updating dynamic required number of annotations for task node {task_node.id_}. "
                f"Current Performance: {model_performance_score}), "
                f"Model Performance is already at its maximum ! "
                f"Setting required images to assigned items count ({required_images})"
            )
        else:
            # If the target performance is greater than 1, then the threshold cannot be calculated as it leads to
            # log(0) or log(-ve value).
            target_performance_score = min(
                MAXIMUM_PERFORMANCE,
                model_performance_score * (1 + PERFORMANCE_INCREASE),
            )

            # Round up to the nearest integer. This is worse case and also ensures that there is at least one image
            required_images = ceil(
                ((log(1 - target_performance_score) / log(1 - model_performance_score)) - 1) * assigned_items_count
            )

            logging.info(
                f"Updating dynamic required number of annotations for task node {task_node.id_}. "
                f"Current performance: {model_performance_score},"
                f"Target performance: {target_performance_score},"
                f"Assigned items count: {assigned_items_count}, "
                f"Required images: {required_images}"
            )

        config.data.required_images_auto_training_dynamic = required_images
        config_param_repo.save(config)
