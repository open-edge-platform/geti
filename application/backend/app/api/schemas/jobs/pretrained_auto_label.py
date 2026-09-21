# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.jobs.models import JobType
from app.models.jobs import PretrainedAutoLabelJob

from .base import BaseJobRequest


class PretrainedAutoLabelRequestParams(BaseModel):
    model_architecture_id: str
    confidence_threshold: float = Field(default=0.25, ge=0, le=1)


class PretrainedAutoLabelRequest(BaseJobRequest):
    job_type: Literal[JobType.PRETRAINED_AUTO_LABEL]
    parameters: PretrainedAutoLabelRequestParams


class PretrainedAutoLabelMetadata(BaseModel):
    project_id: UUID
    model_architecture_id: str

    @model_validator(mode="before")
    @classmethod
    def populate_metadata(cls, data: object) -> object:
        if isinstance(data, PretrainedAutoLabelJob):
            return {
                "project_id": data.project_id,
                "model_architecture_id": data.params.model_architecture_id,
            }
        return data
