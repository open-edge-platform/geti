# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.core.jobs.models import JobParams, JobType, ProjectJob


class PretrainedAutoLabelJobParams(JobParams):
    project_id: UUID
    model_architecture_id: str
    confidence_threshold: float = Field(default=0.25, ge=0, le=1)


class PretrainedAutoLabelJob(ProjectJob[PretrainedAutoLabelJobParams]):
    job_type: Literal[JobType.PRETRAINED_AUTO_LABEL] = JobType.PRETRAINED_AUTO_LABEL  # pyrefly: ignore[bad-override]
    log_dir: Path
    params: PretrainedAutoLabelJobParams
