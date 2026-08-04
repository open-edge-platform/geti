# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class InputData(BaseModel):
    webrtc_id: str
    conf_threshold: float = Field(ge=0, le=1)

    @field_validator("conf_threshold", mode="before")
    @classmethod
    def reject_bool_threshold(cls, v: object) -> object:
        if isinstance(v, bool):
            raise ValueError("conf_threshold must be a number, not a boolean")
        return v


class Offer(BaseModel):
    webrtc_id: str
    sdp: str = Field(min_length=1)
    type: Literal["offer", "pranswer", "answer", "rollback"]


class Answer(BaseModel):
    sdp: str
    type: str
