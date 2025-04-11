# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

from __future__ import annotations

import logging
import os
from enum import Enum
from time import time
from typing import TYPE_CHECKING, Any

from lightning import Callback, LightningModule, Trainer
from mlflow.entities import Run, RunTag

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mlflow import MlflowClient
    from torch import Tensor

from geti_kafka_tools import publish_event

logger = logging.getLogger("mlflow_job")


class TrainingStage(Enum):
    """
    Specifies the current stage of a Training Operation
    """

    INITIALIZATION = 0
    TRAINING = 1
    OPTIMIZATION = 2
    EXPORT = 3
    HYPER_PARAMETER_OPTIMIZATION = 4

    def __str__(self) -> str:
        return str(self.name)


PROGRESS_KEY = "__progress__"
STAGE_KEY = "__stage__"


class ProgressUpdater:
    """
    Progress Updater class

    :param interval: Time interval (seconds) to submit progress report to MLFlow
    """

    def __init__(
        self,
        client: MlflowClient,
        run: Run,
        stage: TrainingStage | None = None,
        n_processes: int = 1,
        interval: float = 2.0,
        complete_per_process: list[int | float] | None = None,
    ) -> None:
        self.client = client
        self.run = run
        self.stage = stage
        self.n_processes = n_processes
        self.interval = interval
        self.timestamp = None
        self._current_process_idx = 0
        if complete_per_process is None:
            self._complete_per_process = [1.0 / self.n_processes] * self.n_processes
        else:
            sum_of_ratio = sum(complete_per_process)
            self._complete_per_process = [val / sum_of_ratio for val in complete_per_process]

    def next_process(self) -> None:
        """
        Increment current inference process indicator.
        """
        if self._current_process_idx + 1 < self.n_processes:
            self._current_process_idx += 1
        else:
            logger.warning("ProgressUpdater is already at the last process. Cannot increment process idx.")

    def update_progress(self, progress: float, score: float | None = None) -> None:  # noqa: ARG002
        """
        Updates the progress of the training in MDS (field in the Operation object) expressed in percents as a float.
        Moreover, this method updated a stage filed in MDS.
        """
        new_timestamp = time()

        if self.timestamp is not None and new_timestamp - self.timestamp < self.interval:
            return

        real_progress = (
            sum(self._complete_per_process[: self._current_process_idx]) * 100
            + progress * self._complete_per_process[self._current_process_idx]
        )

        self.client.log_batch(
            run_id=self.run.info.run_id,
            tags=[
                RunTag(key=PROGRESS_KEY, value=str(real_progress)),
                RunTag(key=STAGE_KEY, value=str(self.stage)),
            ],
            synchronous=False,
        )
        execution_id = os.environ.get("EXECUTION_ID", None)
        task_id = os.environ.get("TASK_ID", None)
        if execution_id is not None and task_id is not None:
            publish_event(
                topic="job_step_details",
                body={
                    "execution_id": execution_id,
                    "task_id": task_id,
                    "progress": real_progress,
                    "message": f"Stage: {str(self.stage).title()}",
                },
                key=self.run.info.run_id.encode(),
                headers_getter=lambda: [
                    ("organization_id", os.environ.get("SESSION_ORGANIZATION_ID").encode("utf-8")),  # type: ignore
                    ("workspace_id", os.environ.get("SESSION_WORKSPACE_ID").encode("utf-8")),  # type: ignore
                    ("source", b"internal"),
                ],
            )

        self.timestamp = new_timestamp  # type: ignore


class ProgressUpdaterCallback(Callback):
    """PyTorchLightining Callback for Geti ProgressUpdater.  A scope of progress is 0 ~ 100"""

    def __init__(self, progress_updater: ProgressUpdater) -> None:
        super().__init__()
        self.progress_updater = progress_updater

    def on_train_start(self, trainer: Trainer, pl_module: LightningModule) -> None:  # noqa: ARG002
        # NOTE: Report when global_rank == 0
        if trainer.global_rank != 0:
            return
        self.progress_updater.update_progress(progress=0.0)

    def on_train_batch_end(
        self,
        trainer: Trainer,
        pl_module: LightningModule,  # noqa: ARG002
        outputs: Tensor | Mapping[str, Any] | None,  # noqa: ARG002
        batch: Any,  # noqa: ARG002
        batch_idx: int,
    ) -> None:
        # NOTE: Report when global_rank == 0
        if trainer.global_rank != 0:
            return
        self.progress_updater.update_progress(progress=self._get_progress(trainer, batch_idx))

    @staticmethod
    def _get_progress(trainer: Trainer, batch_idx: int) -> float:
        return round(((trainer.current_epoch + batch_idx / trainer.num_training_batches) / trainer.max_epochs) * 100, 2)
