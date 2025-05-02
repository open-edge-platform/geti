# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TYPE_CHECKING
from unittest.mock import call, patch

import numpy as np

from active_learning.entities import ActiveScore, ActiveScoreReductionFunction
from active_learning.entities.active_manager.task_active_manager import TaskActiveManager
from active_learning.storage.repos import ActiveScoreRepo

from iai_core_py.entities.annotation_scene_state import AnnotationState
from iai_core_py.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo

if TYPE_CHECKING:
    from active_learning.entities.active_manager.pipeline_active_manager import PipelineActiveManager


class TestPipelineActiveManager:
    def test_get_scores_reduce_fn(self, fxt_pipeline_active_manager) -> None:
        active_manager: PipelineActiveManager = fxt_pipeline_active_manager
        raw_scores = [0.2, 0.3, 0.4]

        # default function: mean
        config = active_manager.get_configuration()
        assert config.inter_task_reduce_fn == ActiveScoreReductionFunction.MEAN
        reduce_fn = active_manager._get_scores_reduce_fn()
        reduced_score = reduce_fn(raw_scores)
        assert isinstance(reduced_score, float)
        assert reduced_score == 0.3

        # custom selection: min
        config.inter_task_reduce_fn = ActiveScoreReductionFunction.MIN
        reduce_fn = active_manager._get_scores_reduce_fn()
        reduced_score = reduce_fn(raw_scores)
        assert isinstance(reduced_score, float)
        assert reduced_score == 0.2

        # custom selection: max
        config.inter_task_reduce_fn = ActiveScoreReductionFunction.MAX
        reduce_fn = active_manager._get_scores_reduce_fn()
        reduced_score = reduce_fn(raw_scores)
        assert isinstance(reduced_score, float)
        assert reduced_score == 0.4

        # empty input
        reduced_score = reduce_fn([])
        assert isinstance(reduced_score, float)
        assert reduced_score == 1.0

    def test_get_unannotated_media_identifiers(self, fxt_pipeline_active_manager, fxt_media_identifier_factory) -> None:
        active_manager: PipelineActiveManager = fxt_pipeline_active_manager
        unannotated_media_identifiers = tuple(fxt_media_identifier_factory(i) for i in range(3))
        with patch.object(
            DatasetStorageFilterRepo,
            "get_media_identifiers_by_annotation_state",
            return_value=iter(unannotated_media_identifiers),
        ) as mock_get_unannotated:
            output = tuple(active_manager._get_unannotated_media_identifiers())

        mock_get_unannotated.assert_called_once_with(annotation_state=AnnotationState.NONE, sample_size=10000)
        assert output == unannotated_media_identifiers

    def test_get_best_candidates(self, fxt_pipeline_active_manager, fxt_media_identifier_factory, fxt_model) -> None:
        active_manager: PipelineActiveManager = fxt_pipeline_active_manager
        id1 = fxt_media_identifier_factory(1)
        id2 = fxt_media_identifier_factory(2)
        id3 = fxt_media_identifier_factory(3)
        with patch.object(
            ActiveScoreRepo,
            "find_best_candidates",
            return_value=((id1, 0.6), (id1, 0.7)),
        ) as mock_find_candidates:
            candidates_ids = active_manager._get_best_candidates(
                candidates=(id1, id2, id3), size=2, models_ids=[fxt_model.id_]
            )

        mock_find_candidates.assert_called_once_with(
            candidate_media=(id1, id2, id3),
            size=2,
            task_node_id=None,
            models_ids=[fxt_model.id_],
            inferred_only=False,
        )
        assert candidates_ids == ((id1, 0.6), (id1, 0.7))

    def test_update_reduced_scores(self, fxt_pipeline_active_manager, fxt_active_score_factory) -> None:
        active_manager: PipelineActiveManager = fxt_pipeline_active_manager
        active_score: ActiveScore = fxt_active_score_factory(index=0)
        assert active_score.pipeline_score == 1.0
        assert len(active_score.tasks_scores) > 1, "Too few tasks, test not significant"
        expected_pipeline_score = min(task_score.score for task_score in active_score.tasks_scores.values())
        with patch.object(active_manager, "_get_scores_reduce_fn", return_value=min):
            active_manager._update_reduced_scores([active_score])

        assert active_score.pipeline_score == expected_pipeline_score

    def test_update_scores(
        self,
        fxt_pipeline_active_manager,
        fxt_active_score_factory,
        fxt_dataset,
        fxt_dataset_non_empty,
        fxt_model,
        fxt_ote_id,
    ) -> None:
        active_manager: PipelineActiveManager = fxt_pipeline_active_manager
        trainable_tasks = active_manager.get_trainable_task_nodes()
        task_id_1 = trainable_tasks[0].id_
        task_id_2 = trainable_tasks[1].id_
        active_scores: list[ActiveScore] = [fxt_active_score_factory(index=i) for i in range(2)]
        unseen_dataset_with_preds_by_task = {
            task_id_1: fxt_dataset_non_empty,
            task_id_2: fxt_dataset_non_empty,
        }
        seen_dataset_items_with_preds_by_task = {
            task_id_1: tuple(fxt_dataset_non_empty),
            task_id_2: tuple(fxt_dataset_non_empty),
        }
        seen_dataset_items_with_annos_by_task = {
            task_id_1: tuple(fxt_dataset_non_empty),
            task_id_2: tuple(fxt_dataset_non_empty),
        }
        unseen_feat_by_task = {
            task_id_1: np.random.rand(len(fxt_dataset_non_empty), 8),
            task_id_2: np.random.rand(len(fxt_dataset_non_empty), 8),
        }
        seen_feat_by_task = {
            task_id_1: np.random.rand(len(fxt_dataset), 8),
            task_id_2: np.random.rand(len(fxt_dataset), 8),
        }
        model_by_task = {
            task_id_1: fxt_model,
            task_id_2: fxt_model,
        }

        with (
            patch.object(TaskActiveManager, "update_scores") as mock_task_update_scores,
            patch.object(active_manager, "_update_reduced_scores") as mock_update_reduced_scores,
            patch.object(ActiveScoreRepo, "save_many") as mock_save_many,
        ):
            active_manager.update_scores(
                scores=active_scores,
                unseen_dataset_with_predictions_by_task=unseen_dataset_with_preds_by_task,
                seen_dataset_items_with_predictions_by_task=seen_dataset_items_with_preds_by_task,
                seen_dataset_items_with_annotations_by_task=seen_dataset_items_with_annos_by_task,
                unseen_dataset_features_by_task=unseen_feat_by_task,
                seen_dataset_features_by_task=seen_feat_by_task,
                model_by_task=model_by_task,
                save=True,
            )

        mock_task_update_scores.assert_has_calls(
            [
                call(
                    scores=active_scores,
                    unseen_dataset_with_predictions=fxt_dataset_non_empty,
                    seen_dataset_items_with_predictions=tuple(fxt_dataset_non_empty),
                    seen_dataset_items_with_annotations=tuple(fxt_dataset),
                    unseen_dataset_features=unseen_feat_by_task[task_id_1],
                    seen_dataset_features=seen_feat_by_task[task_id_1],
                    model=model_by_task[task_id_1],
                    save=False,
                ),
                call(
                    scores=active_scores,
                    unseen_dataset_with_predictions=fxt_dataset_non_empty,
                    seen_dataset_items_with_predictions=tuple(fxt_dataset_non_empty),
                    seen_dataset_items_with_annotations=tuple(fxt_dataset),
                    unseen_dataset_features=unseen_feat_by_task[task_id_2],
                    seen_dataset_features=seen_feat_by_task[task_id_2],
                    model=model_by_task[task_id_2],
                    save=False,
                ),
            ]
        )
        mock_update_reduced_scores.assert_called_once_with(active_scores)
        mock_save_many.assert_called_once_with(active_scores)
