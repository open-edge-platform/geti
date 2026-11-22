# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field, computed_field

from app.core.jobs.models import JobParams, JobType, ProjectJob
from app.models.project import Task
from app.models.system import DeviceInfo


class TrainingJobParams(JobParams):
    job_id: UUID
    project_id: UUID
    model_architecture_id: str
    model_architecture_name: str
    parent_model_revision_id: UUID | None = None
    task: Task
    model_id: UUID = Field(default_factory=uuid4)
    dataset_revision_id: UUID | None = None
    dataset_view_id: UUID | None = None
    # Resolved at submission time so the worker does not need to look the view up again.
    dataset_view_name: str | None = None
    device: DeviceInfo

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_model_revision(self) -> bool:
        return self.parent_model_revision_id is not None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def model_name(self) -> str:
        """User-friendly model name derived from architecture name and model ID."""
        return f"{self.model_architecture_name} ({str(self.model_id).split('-')[0]})"


class TrainingJob(ProjectJob[TrainingJobParams]):
    job_type: Literal[JobType.TRAIN] = JobType.TRAIN  # pyrefly: ignore[bad-override]
    log_dir: Path
    data_dir: Path
    params: TrainingJobParams
