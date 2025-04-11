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

"""This module implements the subclasses of TaskActiveManager"""

import logging
from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import cast

import numpy as np

from active_learning.algorithms import (
    FeatureReconstructionError,
    FeatureReconstructionErrorClassAgnostic,
    IScoringFunction,
)
from active_learning.entities import (
    ActiveLearningTaskConfig,
    ActiveScore,
    ActiveScoreReductionFunction,
    ActiveScoreSuggestionInfo,
    TaskActiveScore,
)
from active_learning.entities.active_manager.base_active_manager import BaseActiveManager
from active_learning.storage.repos import ActiveScoreRepo
from active_learning.utils import NullableDataset
from active_learning.utils.exceptions import FailedActiveScoreUpdate, NoActiveLearningAlgorithmSupported
from communication.constants import MAX_UNANNOTATED_DATASET_SIZE
from communication.exceptions import (
    ModelStorageNotFoundException,
    TaskNotFoundInProjectException,
    TaskNotTrainableException,
)

from geti_types import ID, MediaIdentifierEntity
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.entities.annotation_scene_state import AnnotationState
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.label_schema import LabelSchemaView
from sc_sdk.entities.model import Model
from sc_sdk.entities.model_storage import ModelStorage, NullModelStorage
from sc_sdk.entities.model_template import ModelTemplate, TaskType
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import ConfigurableParametersRepo, ModelStorageRepo
from sc_sdk.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo

logger = logging.getLogger(__name__)


class TaskActiveManager(BaseActiveManager[ActiveLearningTaskConfig]):
    """
    Active suggestion manager for a task.

    It exploits the score extractors defined in the active learning task configuration
    to compute the active scores relative to the task.

    The active manager is designed to be stateless across requests: this class may be
    instantiated for each create/update operation, and it must be destroyed at the end.
    No state shall persist in-memory after each request is served.

    :param workspace_id: ID of the workspace containing the project
    :param project_id: ID of the project containing the media
    :param dataset_storage_id: ID of the dataset storage containing the media
    :param task_id: ID of the task node the manager refers to
    """

    def __init__(
        self,
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        task_id: ID,
    ) -> None:
        super().__init__(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )
        self.task_node_id = task_id

        # Entities are loaded lazily when needed for performance reasons.
        # They are then cached per-request (same lifetime of the active manager)
        self.__task_node: TaskNode | None = None
        self.__model_storage: ModelStorage | None = None
        self.__configuration: ActiveLearningTaskConfig | None = None

    def get_configuration(self) -> ActiveLearningTaskConfig:
        if self.__configuration is None:
            config_repo = ConfigurableParametersRepo(self.project_identifier)
            component_parameters = config_repo.get_or_create_component_parameters(
                data_instance_of=ActiveLearningTaskConfig,
                component=ComponentType.TASK_ACTIVE_LEARNING,
                task_id=self.task_node_id,
            )
            if component_parameters.data is None:
                raise RuntimeError("Failed to initialize task active manager config")
            self.__configuration = component_parameters.data
        return self.__configuration

    def get_task_node(self) -> TaskNode:
        """
        Get the TaskNode entity relative to the active manager.
        If the relative project is not already cached, it is loaded from the repo.

        :return: TaskNode
        """
        if self.__task_node is None:
            self.__task_node = self._get_and_validate_task_node_by_id(task_id=self.task_node_id)
        return self.__task_node

    def get_model_storage(self, model_storage_id: ID) -> ModelStorage:
        """
        Get the ModelStorage entity relative to the active manager.
        If not already cached, it is loaded from the repo.

        :param model_storage_id: ID of the model storage
        :return: ModelStorage
        :raises: ModelStorageNotFoundException if the storage cannot be found
        """
        if self.__model_storage is None:
            model_storage_repo = ModelStorageRepo(self.project_identifier)
            model_storage = model_storage_repo.get_by_id(model_storage_id)
            if isinstance(model_storage, NullModelStorage):
                raise ModelStorageNotFoundException(model_storage_id)
            self.__model_storage = model_storage
        return self.__model_storage

    def _get_and_validate_task_node_by_id(self, task_id: ID) -> TaskNode:
        """
        Find a task node by ID within the specified project

        :param task_id: ID of the task node
        :return: TaskNode
        :raises: ValueError if ('project_id'-'task_id') is not valid for active learning
        """
        project = self.get_project()
        task_node = project.get_trainable_task_node_by_id(task_id)

        if task_node is None:
            # Try to determine why the task node was not found
            task = next((task for task in project.tasks if task.id_ == task_id), None)
            if task is not None:  # active set requested on 'dataset' or 'crop'
                raise TaskNotTrainableException(task_node=task)
            raise TaskNotFoundInProjectException(project=project, task_id=task_id)
        return task_node

    def _get_enabled_scoring_functions(
        self, model_template: ModelTemplate, task_label_schema: LabelSchemaView
    ) -> tuple[type[IScoringFunction], ...]:
        """
        Get the active learning algorithms (scoring functions) to use for this task
        based on:
         - model architecture capabilities (from model template)
         - label schema structure (multiclass, multilabel, ...)
         - configuration

        :param model_template: Template of the model used to generate predictions
        :param task_label_schema: Task-relative label schema
        :return: Tuple of scoring functions to use
        """
        scoring_functions: list[type[IScoringFunction]] = []

        # TODO in the future, 'config_feature_guided_enabled' will be determined
        #  by a configurable parameter; as long as we only have 1 strategy available
        #  (FRE) it is not configurable
        config_feature_guided_enabled = True
        model_feature_guided_supported = model_template.computes_representations()
        if model_feature_guided_supported and config_feature_guided_enabled:
            # For multi-class classification the choice is FRE with labels,
            # for the other cases it is FRE without labels
            is_classification = model_template.task_type == TaskType.CLASSIFICATION
            label_groups = task_label_schema.get_groups(include_empty=True)
            is_multiclass = len(label_groups) == 1
            if is_classification and is_multiclass:
                scoring_functions.append(FeatureReconstructionError)
            else:
                scoring_functions.append(FeatureReconstructionErrorClassAgnostic)

        if not scoring_functions:
            logger.error(
                "No scoring functions available based on configuration and model template '%s' (capabilities '%s').",
                model_template.model_template_id,
                model_template.capabilities,
            )
            raise NoActiveLearningAlgorithmSupported(model_template=model_template)

        return tuple(scoring_functions)

    def _get_scores_reduce_fn(self) -> Callable[[Sequence[float]], float]:
        """
        Get the intra-task score reduction function based on the configuration.

        :return: Function to reduce a sequence of floats to a single one
        """
        config = self.get_configuration()
        reduce_fn_enum: ActiveScoreReductionFunction = config.intra_task_reduce_fn
        return BaseActiveManager.reduce_fn_enum_to_callable(reduce_fn_enum)

    def _get_unannotated_media_identifiers(
        self,
    ) -> list[MediaIdentifierEntity]:
        """
        Find the unannotated media for the current task node.

        :return: Tuple containing the identifiers of the unannotated media.
        """
        prev_trainable_tasks_ids: list[ID] = []
        for prev_task in self.get_trainable_task_nodes():
            if prev_task.id_ == self.task_node_id:
                break
            prev_trainable_tasks_ids.append(prev_task.id_)

        dataset_storage_filter_repo = DatasetStorageFilterRepo(
            dataset_storage_identifier=self.dataset_storage_identifier
        )
        if prev_trainable_tasks_ids:
            # PARTIALLY_ANNOTATED is equipollent to NONE for active learning purposes.
            # For instance, in the second task of det->cls chain, we are interested also in
            # media where some boxes do not have cls label while other ones do.
            media_identifiers = dataset_storage_filter_repo.get_media_identifiers_by_annotation_state(
                annotation_state=AnnotationState.PARTIALLY_ANNOTATED, sample_size=MAX_UNANNOTATED_DATASET_SIZE
            )
        else:
            media_identifiers = dataset_storage_filter_repo.get_media_identifiers_by_annotation_state(
                annotation_state=AnnotationState.NONE, sample_size=MAX_UNANNOTATED_DATASET_SIZE
            )

        return media_identifiers

    def _get_best_candidates(
        self,
        candidates: Sequence[MediaIdentifierEntity],
        size: int,
        models_ids: Sequence[ID] | None = None,
        inferred_only: bool = False,
    ) -> tuple[ActiveScoreSuggestionInfo, ...]:
        return super()._get_best_candidates_impl(
            candidates=candidates,
            size=size,
            task_node_id=self.task_node_id,
            models_ids=models_ids,
            inferred_only=inferred_only,
        )

    def _update_reduced_scores(self, scores: Sequence[ActiveScore]) -> None:
        """
        Iterate over a sequence of ActiveScore entities and overwrite (in-place)
        their task-aggregate score using the respective extractors scores and the
        intra-task reduction function.

        :param scores: ActiveScore entities to update
        """
        reduce_fn = self._get_scores_reduce_fn()
        for score in scores:
            score.refresh_tasks_scores(reduce_fns={self.task_node_id: reduce_fn})

    def update_scores(  # noqa: PLR0913
        self,
        scores: Sequence[ActiveScore],
        unseen_dataset_with_predictions: NullableDataset,
        seen_dataset_items_with_predictions: Sequence[DatasetItem],
        seen_dataset_items_with_annotations: Sequence[DatasetItem],
        unseen_dataset_features: np.ndarray,
        seen_dataset_features: np.ndarray,
        model: Model,
        save: bool = True,
    ) -> None:
        """
        Given predictions and metadata, recompute the active scores for the
        corresponding media up to task level, that is aggregating by media across
        the ROIs and scoring functions.

        The ActiveScore objects passed as input will be overwritten in-place.

        :param scores: ActiveScore items to update
        :param unseen_dataset_with_predictions: Dataset of unlabeled items with
            predictions generated by a model. These samples are "unseen" by the model,
            i.e. the model was not trained on them.
        :param seen_dataset_items_with_predictions: Dataset of "seen" items with predictions
            generated by a model. These are the items on which the model was trained,
            but with predictions from that model rather than user annotation.
        :param seen_dataset_items_with_annotations: Dataset of "seen" items with annotations.
        :param unseen_dataset_features: Feature vectors relative to the unseen dataset.
            If required, it must have the same length of the unseen dataset.
        :param seen_dataset_features: Feature vectors relative to the seen dataset.
            If required, it must have the same length of the seen dataset.
        :param model: Model used for generating the predictions
        :param save: Whether to save or not the scores after the update
        """
        task_node_id = self.task_node_id

        # Find the AL scoring algorithms that are enabled and supported for the task
        scoring_functions = self._get_enabled_scoring_functions(
            model_template=model.model_storage.model_template,
            task_label_schema=cast("LabelSchemaView", model.get_label_schema()),
        )
        scoring_functions_names = {fn.__name__ for fn in scoring_functions}

        # Compute the per-item active scores for each algorithm
        scores_per_item: list[np.ndarray] = []  # one array of scores for each algorithm
        for scoring_fn in scoring_functions:
            try:
                scores_per_fn = scoring_fn.compute_scores(
                    unseen_dataset_with_predictions=unseen_dataset_with_predictions,
                    seen_dataset_items_with_predictions=seen_dataset_items_with_predictions,
                    seen_dataset_items_with_annotations=seen_dataset_items_with_annotations,
                    unseen_dataset_features=unseen_dataset_features,
                    seen_dataset_features=seen_dataset_features,
                )
            except Exception:
                logger.exception(
                    "Failed to compute scores with function '%s'; defaulting to 1.0",
                    scoring_fn.__name__,
                )
                scores_per_fn = np.ones(len(unseen_dataset_with_predictions))
            scores_per_item.append(scores_per_fn)

        # Aggregate the scores relative to different items with the same media
        # (but do not aggregate over the scoring functions yet)
        scores_stacked = np.vstack(scores_per_item)
        scores_per_media = defaultdict(list)
        item: DatasetItem
        for item, item_scores in zip(unseen_dataset_with_predictions, scores_stacked.T):
            scores_per_media[item.media_identifier].append(item_scores)
        scores_per_media_roi_aggr = {
            key: np.minimum.reduce(np.array(values), axis=1) for key, values in scores_per_media.items()
        }

        # Update the actual ActiveScore items with the newly computed values.
        # Any old value relative to non-enabled score extractors will be removed too.
        for score in scores:
            try:
                task_score = score.tasks_scores.get(task_node_id)
                if task_score is None:  # first time active score is recomputed
                    task_score = TaskActiveScore()
                    score.tasks_scores[task_node_id] = task_score
                task_score.model_id = model.id_
                task_score.extractors_scores = {  # filter enabled
                    score_fn_name: old_score_fn_value
                    for score_fn_name, old_score_fn_value in task_score.extractors_scores.items()
                    if score_fn_name in scoring_functions_names
                }
                for score_fn_name, new_score_fn_value in zip(
                    scoring_functions_names,
                    scores_per_media_roi_aggr[score.media_identifier],
                ):
                    task_score.extractors_scores[score_fn_name] = float(new_score_fn_value)
            except Exception as exc:
                raise FailedActiveScoreUpdate from exc

        # Update the per-task aggregated scores
        self._update_reduced_scores(scores)

        # Save the updated scores to the DB
        if save:
            active_score_repo = ActiveScoreRepo(self.dataset_storage_identifier)
            active_score_repo.save_many(scores)
