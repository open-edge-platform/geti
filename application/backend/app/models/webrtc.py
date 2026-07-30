# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field, StrictFloat


class InputData(BaseModel):
    webrtc_id: str
    conf_threshold: StrictFloat = Field(ge=0, le=1)


class Offer(BaseModel):
    webrtc_id: str
    sdp: str = Field(min_length=1)
    type: Literal["offer", "pranswer", "answer", "rollback"]


class Answer(BaseModel):
    sdp: str
    type: str
