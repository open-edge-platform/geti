# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import contextlib
from contextlib import AbstractContextManager, nullcontext
from copy import copy
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import numpy as np
import pytest

from active_learning.algorithms import FeatureReconstructionError, FeatureReconstructionErrorClassAgnostic
from active_learning.entities import ActiveScore, ActiveScoreReductionFunction
from active_learning.storage.repos import ActiveScoreRepo
from active_learning.utils.exceptions import NoActiveLearningAlgorithmSupported
from communication.exceptions import TaskNotFoundInProjectException, TaskNotTrainableException

from iai_core.entities.annotation_scene_state import AnnotationState
from iai_core.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo

if TYPE_CHECKING:
    from _pytest.python_api import RaisesContext

    from active_learning.entities.active_manager.task_active_manager import TaskActiveManager

    from iai_core.entities.datasets import Dataset
    from iai_core.entities.label_schema import LabelSchemaView
    from iai_core.entities.model_template import ModelTemplate


def do_nothing(*args, **kwargs):
    pass


class TestTaskActiveManager:
    def test_find_and_validate_task_node(self, fxt_task_active_manager, fxt_ote_id) -> None:
        active_manager: TaskActiveManager = fxt_task_active_manager
        good_task_id = active_manager.task_node_id
        non_trainable_task_id = active_manager.get_project().tasks[0].id_
        non_existing_task_id = fxt_ote_id(123456)

        found_task_node = active_manager._get_and_validate_task_node_by_id(task_id=good_task_id)
        assert found_task_node == active_manager.get_task_node()

        with pytest.raises(TaskNotTrainableException):
            active_manager._get_and_validate_task_node_by_id(task_id=non_trainable_task_id)

        with pytest.raises(TaskNotFoundInProjectException):
            active_manager._get_and_validate_task_node_by_id(task_id=non_existing_task_id)

    @pytest.mark.parametrize(
        "task_type, expected_functions",
        (
            ("multiclass classification", (FeatureReconstructionError,)),
            ("multilabel classification", (FeatureReconstructionErrorClassAgnostic,)),
            ("detection", (FeatureReconstructionErrorClassAgnostic,)),
            ("segmentation", (FeatureReconstructionErrorClassAgnostic,)),
            ("anomaly", None),
        ),
        ids=[
            "multiclass classification",
            "multilabel classification",
            "detection",
            "segmentation",
            "anomaly (unsupported)",
        ],
    )
    def test_get_enabled_scoring_functions(
        self,
        fxt_task_active_manager,
        task_type,
        expected_functions,
        fxt_model_template_classification,
        fxt_model_template_detection,
        fxt_model_template_segmentation,
        fxt_model_template_anomaly_classification,
        fxt_classification_label_schema_factory,
        fxt_detection_label_schema_factory,
        fxt_segmentation_label_schema_factory,
        fxt_anomaly_classificaction_label_schema,
    ) -> None:
        active_manager: TaskActiveManager = fxt_task_active_manager

        model_template: ModelTemplate
        label_schema: LabelSchemaView
        if task_type == "multiclass classification":
            model_template = fxt_model_template_classification
            label_schema = fxt_classification_label_schema_factory(multilabel=False)
        elif task_type == "multilabel classification":
            model_template = fxt_model_template_classification
            label_schema = fxt_classification_label_schema_factory(multilabel=True)
        elif task_type == "detection":
            model_template = fxt_model_template_detection
            label_schema = fxt_detection_label_schema_factory()
        elif task_type == "segmentation":
            model_template = fxt_model_template_segmentation
            label_schema = fxt_segmentation_label_schema_factory()
        elif task_type == "anomaly":
            model_template = fxt_model_template_anomaly_classification
            label_schema = fxt_anomaly_classificaction_label_schema
        else:
            raise ValueError(f"Invalid task type {task_type}")

        exception_context: AbstractContextManager | RaisesContext
        if expected_functions is None:
            exception_context = pytest.raises(NoActiveLearningAlgorithmSupported)
        else:
            exception_context = contextlib.nullcontext()

        with exception_context:
            scoring_functions = active_manager._get_enabled_scoring_functions(
                model_template=model_template,
                task_label_schema=label_schema,
            )

            assert scoring_functions == expected_functions

    def test_get_scores_reduce_fn(self, fxt_task_active_manager) -> None:
        active_manager: TaskActiveManager = fxt_task_active_manager
        raw_scores = [0.2, 0.3, 0.4]

        # default function: mean
        config = active_manager.get_configuration()
        assert config.intra_task_reduce_fn == ActiveScoreReductionFunction.MEAN
        reduce_fn = active_manager._get_scores_reduce_fn()
        reduced_score = reduce_fn(raw_scores)
        assert isinstance(reduced_score, float)
        assert reduced_score == 0.3

        # custom selection: min
        config.intra_task_reduce_fn = ActiveScoreReductionFunction.MIN
        reduce_fn = active_manager._get_scores_reduce_fn()
        reduced_score = reduce_fn(raw_scores)
        assert isinstance(reduced_score, float)
        assert reduced_score == 0.2

        # custom selection: max
        config.intra_task_reduce_fn = ActiveScoreReductionFunction.MAX
        reduce_fn = active_manager._get_scores_reduce_fn()
        reduced_score = reduce_fn(raw_scores)
        assert isinstance(reduced_score, float)
        assert reduced_score == 0.4

        # empty input
        reduced_score = reduce_fn([])
        assert isinstance(reduced_score, float)
        assert reduced_score == 1.0

    @pytest.mark.parametrize(
        "is_chain_project",
        [False, True],
        ids=["single-task project", "task-chain project"],
    )
    def test_get_unannotated_media_identifiers(
        self,
        is_chain_project,
        fxt_task_active_manager,
        fxt_annotation_scene_state,
        fxt_media_identifier,
        fxt_segmentation_task,
        mock_annotation_scene_state_repo,
    ) -> None:
        active_manager: TaskActiveManager = fxt_task_active_manager
        this_task = active_manager.get_task_node()

        patch_project_get_trainable_task_nodes: Any
        if is_chain_project:
            prev_task = fxt_segmentation_task
            patch_project_get_trainable_task_nodes = patch.object(
                fxt_task_active_manager.get_project(),
                "get_trainable_task_nodes",
                return_value=[prev_task, this_task],
            )
        else:
            prev_task = None
            patch_project_get_trainable_task_nodes = nullcontext()

        with (
            patch_project_get_trainable_task_nodes,
            patch.object(
                DatasetStorageFilterRepo,
                "get_media_identifiers_by_annotation_state",
                return_value=[fxt_media_identifier],
            ) as mock_get_media_identifiers,
        ):
            media_identifiers = tuple(active_manager._get_unannotated_media_identifiers())

        assert media_identifiers == (fxt_media_identifier,)
        if is_chain_project:
            mock_get_media_identifiers.assert_called_once_with(
                annotation_state=AnnotationState.PARTIALLY_ANNOTATED, sample_size=10000
            )
        else:
            mock_get_media_identifiers.assert_called_once_with(annotation_state=AnnotationState.NONE, sample_size=10000)

    def test_get_best_candidates(self, fxt_task_active_manager, fxt_media_identifier_factory, fxt_model) -> None:
        active_manager: TaskActiveManager = fxt_task_active_manager
        id1 = fxt_media_identifier_factory(1)
        id2 = fxt_media_identifier_factory(2)
        id3 = fxt_media_identifier_factory(3)
        with patch.object(
            ActiveScoreRepo,
            "find_best_candidates",
            return_value=((id1, 0.6), (id1, 0.7)),
        ) as mock_find_candidates:
            candidates_ids = active_manager._get_best_candidates(
                candidates=(id1, id2, id3),
                size=2,
                models_ids=[fxt_model.id_],
            )

        mock_find_candidates.assert_called_once_with(
            candidate_media=(id1, id2, id3),
            size=2,
            task_node_id=active_manager.task_node_id,
            models_ids=[fxt_model.id_],
            inferred_only=False,
        )
        assert candidates_ids == ((id1, 0.6), (id1, 0.7))

    def test_update_reduced_scores(self, fxt_task_active_manager, fxt_active_score_factory) -> None:
        active_manager: TaskActiveManager = fxt_task_active_manager
        active_score: ActiveScore = fxt_active_score_factory(index=0, task_node_id=active_manager.task_node_id)
        assert active_score.tasks_scores[active_manager.task_node_id].score == 0.1
        with patch.object(active_manager, "_get_scores_reduce_fn", return_value=min):
            active_manager._update_reduced_scores([active_score])

        assert active_score.tasks_scores[active_manager.task_node_id].score == 0.2

    def test_update_scores(
        self,
        fxt_task_active_manager,
        fxt_active_score_factory,
        fxt_dataset_storage,
        fxt_dataset_non_empty,
        fxt_model,
        fxt_ote_id,
    ) -> None:
        active_manager: TaskActiveManager = fxt_task_active_manager
        model = fxt_model
        unseen_dataset_with_predictions = copy(fxt_dataset_non_empty)
        seen_dataset_with_predictions = copy(fxt_dataset_non_empty)
        seen_dataset_with_annotations: Dataset = copy(fxt_dataset_non_empty)
        unseen_dataset_with_predictions.id_ = fxt_ote_id(101)
        seen_dataset_with_predictions.id_ = fxt_ote_id(102)
        seen_dataset_with_annotations.id_ = fxt_ote_id(103)
        unseen_features = np.ones(len(unseen_dataset_with_predictions))
        seen_features = np.ones(len(seen_dataset_with_predictions))
        scores_vector = np.random.rand(len(unseen_dataset_with_predictions))
        active_scores: list[ActiveScore] = [
            fxt_active_score_factory(
                index=i,
                media_identifier=unseen_item.media_identifier,
                task_node_id=active_manager.task_node_id,
            )
            for i, unseen_item in enumerate(unseen_dataset_with_predictions)
        ]

        with (
            patch.object(
                active_manager,
                "_get_enabled_scoring_functions",
                return_value=(FeatureReconstructionError,),
            ) as mock_get_scoring_functions,
            patch.object(
                FeatureReconstructionError, "compute_scores", return_value=scores_vector
            ) as mock_compute_scores,
            patch.object(
                active_manager,
                "_update_reduced_scores",
            ) as mock_update_reduced_scores,
            patch.object(ActiveScoreRepo, "save_many") as mock_save_many,
        ):
            active_manager.update_scores(
                scores=active_scores,
                unseen_dataset_with_predictions=unseen_dataset_with_predictions,
                seen_dataset_items_with_predictions=tuple(item for item in seen_dataset_with_predictions),
                seen_dataset_items_with_annotations=tuple(item for item in seen_dataset_with_annotations),
                unseen_dataset_features=unseen_features,
                seen_dataset_features=seen_features,
                model=model,
            )

        mock_get_scoring_functions.assert_called_once_with(
            model_template=model.model_storage.model_template,
            task_label_schema=model.get_label_schema(),
        )
        mock_compute_scores.assert_called_once_with(
            unseen_dataset_with_predictions=unseen_dataset_with_predictions,
            seen_dataset_items_with_predictions=tuple(item for item in seen_dataset_with_predictions),
            seen_dataset_items_with_annotations=tuple(item for item in seen_dataset_with_annotations),
            unseen_dataset_features=unseen_features,
            seen_dataset_features=seen_features,
        )
        mock_update_reduced_scores.assert_called_once_with(active_scores)
        mock_save_many.assert_called_once_with(active_scores)
