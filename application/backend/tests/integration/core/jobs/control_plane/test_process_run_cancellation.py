# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import time
from collections.abc import Callable
from functools import partialmethod
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.core.jobs.control_plane import JobController, JobQueue
from app.core.jobs.exec import ProcessRun, ProcessRunnerFactory
from app.core.jobs.models import JobStatus, JobType
from app.core.run import ExecutionContext, RunnableFactory
from app.models import Task, TaskType, TrainingJob, TrainingJobParams
from app.models.system import DeviceInfo, DeviceType


class UnresponsiveTraining:
    """Reports progress once, then blocks without reporting, so the cancel flag is never observed."""

    def run(self, ctx: ExecutionContext) -> None:
        ctx.report("training", 10.0, None)
        time.sleep(60)


async def _wait_until(predicate: Callable[[], bool], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            raise TimeoutError
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_force_killed_cancelled_training_runs_completion_hook(tmp_path, monkeypatch):
    """A training that ignores cancellation is terminated, and its workspace and status are still reconciled."""
    monkeypatch.setattr(ProcessRun, "stop", partialmethod(ProcessRun.stop, graceful_timeout=1.0))
    data_dir, log_dir = tmp_path / "data", tmp_path / "logs"
    data_dir.mkdir()
    log_dir.mkdir()
    job_id, project_id = uuid4(), uuid4()
    job = TrainingJob(
        id=job_id,
        project_id=project_id,
        log_dir=log_dir,
        data_dir=data_dir,
        params=TrainingJobParams(
            device=DeviceInfo(type=DeviceType.CPU, name="cpu", memory=0, index=None),
            model_architecture_id="test_arch",
            model_architecture_name="Test Arch",
            task=Task(task_type=TaskType.CLASSIFICATION),
            job_id=job_id,
            project_id=project_id,
        ),
    )
    workspace = data_dir / f"getitune-workspace-{job.params.model_id}"
    workspace.mkdir()
    runnables = RunnableFactory()
    runnables.register(JobType.TRAIN, UnresponsiveTraining)
    queue = JobQueue()
    controller = JobController(queue, ProcessRunnerFactory(runnables), max_parallel_jobs=1)

    with patch.object(TrainingJob, "_reconcile_stuck_training_status") as reconcile:
        await controller.start()
        try:
            await queue.submit(job)
            await _wait_until(lambda: job.progress >= 10.0, timeout=120)
            queue.cancel(job.id)
            await _wait_until(lambda: job.status >= JobStatus.DONE, timeout=60)
        finally:
            await controller.stop()

    assert job.status == JobStatus.CANCELLED
    reconcile.assert_called_once()
    assert not workspace.exists()
