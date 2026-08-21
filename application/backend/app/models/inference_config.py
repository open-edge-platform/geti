# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field


class InferenceConfig(BaseModel):
    """
    Inference-time configuration of a pipeline.

    Attributes:
        confidence_threshold: Minimum confidence a prediction must reach to be kept. It defaults to the
            threshold determined when the model was exported (embedded in the model files), and it is
            reset to that default whenever the pipeline switches to another model or model variant.
            None when no model is configured, or when the model does not use a confidence threshold.
    """

    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
