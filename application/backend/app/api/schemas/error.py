# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from pydantic import BaseModel


class APIErrorResponse(BaseModel):
    detail: str | list[dict[str, Any]]
