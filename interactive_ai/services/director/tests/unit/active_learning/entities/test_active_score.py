# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import copy
import logging
from typing import TYPE_CHECKING

import numpy as np
import pytest

if TYPE_CHECKING:
    from active_learning.entities import ActiveScore

logger = logging.getLogger(__name__)


class TestActiveScore:
    def test_init(self, fxt_ote_id, fxt_active_score, fxt_media_identifier) -> None:
        active_score: ActiveScore = fxt_active_score
        model_1_id, model_2_id = fxt_ote_id(1), fxt_ote_id(2)
        task_1_id, task_2_id = fxt_ote_id(3), fxt_ote_id(4)

        assert active_score.id_ == fxt_media_identifier.as_id()
        assert active_score.media_identifier == fxt_media_identifier
        assert active_score.pipeline_score == 0.7
        assert active_score.tasks_scores[task_1_id].model_id == model_1_id
        assert active_score.tasks_scores[task_1_id].score == 0.1
        assert active_score.tasks_scores[task_1_id].extractors_scores["extr_1"] == 0.2
        assert active_score.tasks_scores[task_1_id].extractors_scores["extr_2"] == 0.4
        assert active_score.tasks_scores[task_2_id].model_id == model_2_id
        assert active_score.tasks_scores[task_2_id].score == 0.9
        assert active_score.tasks_scores[task_2_id].extractors_scores["extr_1"] == 0.4
        assert active_score.tasks_scores[task_2_id].extractors_scores["extr_2"] == 0.6

    def test_eq(self, fxt_ote_id, fxt_active_score) -> None:
        active_score: ActiveScore = fxt_active_score
        model_2_id = fxt_ote_id(2)
        task_1_id = fxt_ote_id(3)

        # Test equality
        active_score_copy = copy.deepcopy(active_score)
        assert active_score == active_score_copy

        # Inequality on pipeline-level properties
        attr_new_values = {"pipeline_score": 0.99}
        for attr, new_value in attr_new_values.items():
            logging.info(f"Setting `{attr}` to `{new_value}`")
            active_score_copy = copy.deepcopy(active_score)
            setattr(active_score_copy, attr, new_value)
            assert active_score_copy != active_score

        # Inequality on task-level properties
        attr_new_values = {
            "model_id": model_2_id,
            "score": 0.99,
        }
        for attr, new_value in attr_new_values.items():
            logging.info(f"Setting task `{attr}` to `{new_value}`")
            active_score_copy = copy.deepcopy(active_score)
            setattr(active_score_copy.tasks_scores[task_1_id], attr, new_value)
            assert active_score_copy != active_score

        # Inequality on extractor-level properties
        attr, new_value = "score", 0.99
        logging.info(f"Setting score extractor `{attr}` to `{new_value}`")
        active_score_copy = copy.deepcopy(active_score)
        active_score_copy.tasks_scores[task_1_id].extractors_scores["extr_1"] = new_value
        assert active_score_copy != active_score

    @pytest.mark.parametrize(
        "reduce_fn, expected_score_1, expected_score_2",
        [
            (np.nanmean, 0.3, 0.5),
            (np.nanmin, 0.2, 0.4),
        ],
    )
    def test_refresh_tasks_scores(
        self,
        fxt_ote_id,
        fxt_active_score,
        reduce_fn,
        expected_score_1,
        expected_score_2,
    ) -> None:
        active_score: ActiveScore = fxt_active_score
        task_1_id, task_2_id = fxt_ote_id(3), fxt_ote_id(4)
        tasks_reduce_fns = {
            task_1_id: reduce_fn,
            task_2_id: reduce_fn,
        }

        active_score.refresh_tasks_scores(tasks_reduce_fns)

        assert abs(active_score.tasks_scores[task_1_id].score - expected_score_1) < 1e-6
        assert abs(active_score.tasks_scores[task_2_id].score - expected_score_2) < 1e-6

    @pytest.mark.parametrize(
        "reduce_fn, refresh_tasks, expected_score",
        [
            (np.nanmean, False, 0.5),
            (np.nanmean, True, 0.4),
            (np.nanmin, False, 0.1),
            (np.nanmin, True, 0.2),
        ],
    )
    def test_refresh_pipeline_score(
        self, fxt_active_score, fxt_ote_id, reduce_fn, refresh_tasks, expected_score
    ) -> None:
        active_score: ActiveScore = fxt_active_score
        task_1_id, task_2_id = fxt_ote_id(3), fxt_ote_id(4)
        tasks_reduce_fns = {
            task_1_id: reduce_fn,
            task_2_id: reduce_fn,
        }

        active_score.refresh_pipeline_score(
            reduce_fn=reduce_fn,
            refresh_tasks_scores=refresh_tasks,
            tasks_reduce_fns=tasks_reduce_fns,
        )

        assert abs(active_score.pipeline_score - expected_score) < 1e-6
