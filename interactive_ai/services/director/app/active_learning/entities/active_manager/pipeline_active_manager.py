# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

"""This module implements the subclasses of PipelineActiveManager"""

import logging
from collections.abc import Callable, Mapping, Sequence

import numpy as np

from active_learning.entities import (
    ActiveLearningProjectConfig,
    ActiveScore,
    ActiveScoreReductionFunction,
    ActiveScoreSuggestionInfo,
)
from active_learning.storage.repos import ActiveScoreRepo
from active_learning.utils import NullableDataset
from active_learning.utils.exceptions import FailedActiveScoreUpdate
from communication.constants import MAX_UNANNOTATED_DATASET_SIZE

from .base_active_manager import BaseActiveManager
from .task_active_manager import TaskActiveManager
from geti_types import ID, MediaIdentifierEntity
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.entities.annotation_scene_state import AnnotationState
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.model import Model
from sc_sdk.repos import ConfigurableParametersRepo
from sc_sdk.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo

logger = logging.getLogger(__name__)


class PipelineActiveManager(BaseActiveManager[ActiveLearningProjectConfig]):  # type: ignore[type-arg]
    """
    Active suggestion manager for the full pipeline of tasks in a project.

    It exploits the scores computed by the task active managers of the respective
    task nodes to generate per-media scores aggregated at the project level.

    The active manager is designed to be stateless across requests: this class may be
    instantiated for each create/update operation, and it must be destroyed at the end.
    No state shall persist in-memory after each request is served.

    :param workspace_id: ID of the workspace containing the project
    :param project_id: ID of the project containing the media
    :param dataset_storage_id: ID of the dataset storage containing the media
    """

    def __init__(
        self,
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
    ) -> None:
        super().__init__(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )

        # Entities are loaded lazily when needed for performance reasons.
        # They are then cached per-request (same lifetime of the active manager)
        self.__task_active_managers: dict[ID, TaskActiveManager] | None = None
        self.__configuration: ActiveLearningProjectConfig | None = None

    def get_configuration(self) -> ActiveLearningProjectConfig:
        if self.__configuration is None:
            config_repo = ConfigurableParametersRepo(self.project_identifier)
            component_parameters = config_repo.get_or_create_component_parameters(
                data_instance_of=ActiveLearningProjectConfig,
                component=ComponentType.PROJECT_ACTIVE_LEARNING,
            )
            if component_parameters.data is None:
                raise RuntimeError("Failed to initialize project active manager config")
            self.__configuration = component_parameters.data
        return self.__configuration

    def get_task_active_managers(self) -> dict[ID, TaskActiveManager]:
        """
        Get the task active manager for each trainable task node in the project

        :return: Dict mapping each trainable task node ID to its TaskActiveManager
        """
        if self.__task_active_managers is None:
            self.__task_active_managers = {
                task_node.id_: TaskActiveManager(
                    workspace_id=self.workspace_id,
                    project_id=self.project_id,
                    dataset_storage_id=self.dataset_storage_id,
                    task_id=task_node.id_,
                )
                for task_node in self.get_trainable_task_nodes()
            }
        return self.__task_active_managers

    def _get_scores_reduce_fn(self) -> Callable[[Sequence[float]], float]:
        """
        Get the inter-task score reduction function based on the configuration.

        :return: Function to reduce a sequence of floats to a single one
        """
        config = self.get_configuration()
        reduce_fn_enum: ActiveScoreReductionFunction = config.inter_task_reduce_fn
        return BaseActiveManager.reduce_fn_enum_to_callable(reduce_fn_enum)

    def _get_unannotated_media_identifiers(self) -> list[MediaIdentifierEntity]:
        """
        Find the unannotated media for the current task node.

        :return: Tuple containing the identifiers of the unannotated media.
        """
        dataset_storage_filter_repo = DatasetStorageFilterRepo(
            dataset_storage_identifier=self.dataset_storage_identifier
        )
        return dataset_storage_filter_repo.get_media_identifiers_by_annotation_state(
            annotation_state=AnnotationState.NONE, sample_size=MAX_UNANNOTATED_DATASET_SIZE
        )

    def _get_best_candidates(
        self,
        candidates: Sequence[MediaIdentifierEntity],
        size: int,
        models_ids: Sequence[ID] | None = None,
        inferred_only: bool = False,
    ) -> tuple[ActiveScoreSuggestionInfo, ...]:
        return self._get_best_candidates_impl(
            candidates=candidates,
            size=size,
            models_ids=models_ids,
            inferred_only=inferred_only,
        )

    def _update_reduced_scores(self, scores: Sequence[ActiveScore]) -> None:
        """
        Iterate over a sequence of ActiveScore entities and overwrite (in-place)
        their pipeline-aggregate score using the respective per-task scores and the
        inter-task reduction function.

        :param scores: ActiveScore entities to update
        """
        reduce_fn = self._get_scores_reduce_fn()
        for score in scores:
            score.refresh_pipeline_score(reduce_fn, refresh_tasks_scores=False)

    def __validate_update_scores_input_dicts(
        self,
        unseen_dataset_with_predictions_by_task: Mapping[ID, NullableDataset],
        seen_dataset_items_with_predictions_by_task: Mapping[ID, Sequence[DatasetItem]],
        seen_dataset_items_with_annotations_by_task: Mapping[ID, Sequence[DatasetItem]],
        model_by_task: Mapping[ID, Model],
        unseen_dataset_features_by_task: Mapping[ID, np.ndarray],
        seen_dataset_features_by_task: Mapping[ID, np.ndarray],
    ) -> None:
        """Check that all the input dicts point to the same set of existing tasks"""
        unseen_with_preds_keys = set(unseen_dataset_with_predictions_by_task.keys())
        seen_with_preds_keys = set(seen_dataset_items_with_predictions_by_task.keys())
        seen_with_annos_keys = set(seen_dataset_items_with_annotations_by_task.keys())
        unseen_feat_keys = set(unseen_dataset_features_by_task.keys())
        seen_feat_keys = set(seen_dataset_features_by_task.keys())
        model_keys = set(model_by_task.keys())
        if (
            unseen_with_preds_keys != seen_with_preds_keys
            or unseen_with_preds_keys != seen_with_annos_keys
            or unseen_with_preds_keys != unseen_feat_keys
            or unseen_with_preds_keys != seen_feat_keys
            or unseen_with_preds_keys != model_keys
        ):
            logger.error(
                "Mismatching keys (task node IDs) in the arguments of update_scores: "
                f"unseen dataset with predictions=`{unseen_with_preds_keys}`; "
                f"seen dataset with predictions=`{seen_with_preds_keys}`; "
                f"seen dataset with annotations=`{seen_with_annos_keys}`; "
                f"unseen features=`{unseen_feat_keys}`; "
                f"seen features=`{seen_feat_keys}`; "
                f"models=`{model_keys}`; "
            )
            raise ValueError("Invalid data to update active scores at project level")

        existing_task_nodes_ids = {task_node.id_ for task_node in self.get_trainable_task_nodes()}
        if not unseen_with_preds_keys.issubset(existing_task_nodes_ids):
            logger.error(
                "Some keys (task node IDs) in the arguments of update_scores do not "
                f"map to any of the trainable task nodes of project with ID "
                f"`{self.project_id}`: args keys=`{unseen_with_preds_keys}`; "
                f"existing task nodes IDs=`{existing_task_nodes_ids}`"
            )
            raise ValueError("Invalid data to update active scores at project level")

    def update_scores(  # noqa: PLR0913
        self,
        scores: Sequence[ActiveScore],
        unseen_dataset_with_predictions_by_task: Mapping[ID, NullableDataset],
        seen_dataset_items_with_predictions_by_task: Mapping[ID, Sequence[DatasetItem]],
        seen_dataset_items_with_annotations_by_task: Mapping[ID, Sequence[DatasetItem]],
        unseen_dataset_features_by_task: Mapping[ID, np.ndarray],
        seen_dataset_features_by_task: Mapping[ID, np.ndarray],
        model_by_task: Mapping[ID, Model],
        save: bool = True,
    ) -> None:
        """
        Update the active scores up to project level given predictions (output dataset)
        and metadata for one or more tasks.

        The ActiveScore objects passed as input will be overwritten in-place.

        :param scores: ActiveScore items to update
        :param unseen_dataset_with_predictions_by_task: Dict mapping IDs of task nodes
            to the respective dataset of unlabeled items with predictions generated
            by a model. These samples are "unseen" by the model, i.e. the model was not
            trained on them.
        :param seen_dataset_items_with_predictions_by_task: Dict mapping IDs of task nodes
            to the respective dataset of "seen" items with predictions generated
            by a model. These are the items on which the model was trained,
            but with predictions from that model rather than user annotation.
        :param seen_dataset_items_with_annotations_by_task: Dict mapping IDs of task nodes
            to the respective dataset of "seen" items with annotations.
        :param unseen_dataset_features_by_task: Dict mapping IDs of task nodes
            to the respective feature vectors relative to the unseen dataset.
            If required, it must have the same length of the unseen dataset.
        :param seen_dataset_features_by_task: Dict mapping IDs of task nodes
            to the respective feature vectors relative to the seen dataset.
            If required, it must have the same length of the seen dataset.
        :param model_by_task: Dict mapping IDs of task nodes to the respective
            model used for generating the predictions
        :param save: Whether to save or not the scores after the update
        """
        task_active_managers = self.get_task_active_managers()

        self.__validate_update_scores_input_dicts(
            unseen_dataset_with_predictions_by_task=unseen_dataset_with_predictions_by_task,
            seen_dataset_items_with_predictions_by_task=seen_dataset_items_with_predictions_by_task,
            seen_dataset_items_with_annotations_by_task=seen_dataset_items_with_annotations_by_task,
            unseen_dataset_features_by_task=unseen_dataset_features_by_task,
            seen_dataset_features_by_task=seen_dataset_features_by_task,
            model_by_task=model_by_task,
        )

        # Update the scores up to task level, exploiting the task active managers
        any_task_update_succeeded: bool = False
        for task_node_id in unseen_dataset_with_predictions_by_task:
            task_active_manager = task_active_managers[task_node_id]
            try:
                task_active_manager.update_scores(
                    scores=scores,
                    unseen_dataset_with_predictions=unseen_dataset_with_predictions_by_task[task_node_id],
                    seen_dataset_items_with_predictions=seen_dataset_items_with_predictions_by_task[task_node_id],
                    seen_dataset_items_with_annotations=seen_dataset_items_with_annotations_by_task[task_node_id],
                    unseen_dataset_features=unseen_dataset_features_by_task[task_node_id],
                    seen_dataset_features=seen_dataset_features_by_task[task_node_id],
                    model=model_by_task[task_node_id],
                    save=False,
                )
                any_task_update_succeeded = True
            except FailedActiveScoreUpdate:
                logger.exception("Failed to update active scores for task '%s'", task_node_id)

        if not any_task_update_succeeded:
            logger.error("The active scores could not be updated for any task.")
            raise FailedActiveScoreUpdate

        # Update the per-project aggregated scores
        self._update_reduced_scores(scores)

        # Save the updated scores to the DB
        if save:
            active_score_repo = ActiveScoreRepo(self.dataset_storage_identifier)
            active_score_repo.save_many(scores)
