# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest
from lightning import Trainer as LightningTrainer

from app.execution.training.progress import TestingProgressCallback, TrainingProgressCallback


class DummyTrainer:
    def __init__(self, max_epochs: int | None, num_training_batches: int):
        self.max_epochs = max_epochs
        self.num_training_batches = num_training_batches


def _make_trainer(max_epochs: int | None = 5, num_training_batches: int = 10) -> LightningTrainer:
    return DummyTrainer(max_epochs=max_epochs, num_training_batches=num_training_batches)  # type: ignore[return-value]


class TestTrainingProgressCallback:
    def test_emit_progress_does_nothing_when_total_steps_none(self) -> None:
        report_progress = Mock()
        cb = TrainingProgressCallback(report_progress)

        cb._emit_progress()

        report_progress.assert_not_called()

    def test_on_train_batch_end_emits_progress_in_range(self) -> None:
        report_progress = Mock()
        cb = TrainingProgressCallback(report_progress, min_p=10.0, max_p=80.0)

        trainer = _make_trainer(max_epochs=2, num_training_batches=5)

        for i in range(3):
            cb.on_train_batch_end(
                trainer=trainer,
                pl_module=Mock(),
                outputs=Mock(),
                batch=Mock(),
                batch_idx=i,
            )

        assert cb._current_step == 3
        assert cb._total_steps == 10

        calls = report_progress.call_args_list
        assert len(calls) == 3

        # progress = min_p + (step / total) * (max_p - min_p)
        # steps: 1, 2, 3 (because we increment before emit)
        expected = [
            10.0 + (1 / 10) * 70.0,
            10.0 + (2 / 10) * 70.0,
            10.0 + (3 / 10) * 70.0,
        ]
        actual = [c.args[0] for c in calls]
        assert actual == expected

    def test_on_train_batch_end_respects_custom_progress_bounds(self) -> None:
        report_progress = Mock()
        cb = TrainingProgressCallback(report_progress, min_p=0.0, max_p=100.0)

        trainer = _make_trainer(max_epochs=1, num_training_batches=4)

        for i in range(4):
            cb.on_train_batch_end(
                trainer=trainer,
                pl_module=Mock(),
                outputs=Mock(),
                batch=Mock(),
                batch_idx=i,
            )

        expected = [25.0, 50.0, 75.0, 100.0]
        actual = [c.args[0] for c in report_progress.call_args_list]
        assert actual == expected


class TestTestingProgressCallback:
    def test_emit_progress_does_nothing_before_batch_count_is_initialized(self) -> None:
        report_progress = Mock()
        callback = TestingProgressCallback(report_progress)

        callback._emit_progress()

        report_progress.assert_not_called()

    @pytest.mark.parametrize("num_test_batches", [4, [4], [1, 3], [2, 0, 2]])
    @pytest.mark.parametrize(("min_p", "max_p"), [(0.0, 100.0), (85.0, 90.0), (10.0, 80.0)])
    def test_reports_every_batch_across_test_dataloaders(
        self, num_test_batches: int | list[int], min_p: float, max_p: float
    ) -> None:
        report_progress = Mock()
        callback = TestingProgressCallback(report_progress, min_p=min_p, max_p=max_p)
        trainer = Mock(spec=LightningTrainer)
        trainer.num_test_batches = num_test_batches
        counts = num_test_batches if isinstance(num_test_batches, list) else [num_test_batches]

        for dataloader_idx, count in enumerate(counts):
            for batch_idx in range(count):
                callback.on_test_batch_end(
                    trainer=trainer,
                    pl_module=Mock(),
                    outputs=None,
                    batch=Mock(),
                    batch_idx=batch_idx,
                    dataloader_idx=dataloader_idx,
                )

        total_batches = sum(counts)
        actual = [call.args[0] for call in report_progress.call_args_list]
        expected = [min_p + (step / total_batches) * (max_p - min_p) for step in range(1, total_batches + 1)]
        assert actual == pytest.approx(expected)
        assert actual == sorted(actual)
        assert actual[-1] == max_p
        assert callback._total_steps == total_batches
        assert callback._current_step == total_batches

    @pytest.mark.parametrize("num_test_batches", [0, [], [0, 0]])
    def test_empty_batch_counts_use_nonzero_total(self, num_test_batches: int | list[int]) -> None:
        callback = TestingProgressCallback(Mock())
        trainer = Mock(spec=LightningTrainer)
        trainer.num_test_batches = num_test_batches

        callback._update_total_steps(trainer)

        assert callback._total_steps == 1
