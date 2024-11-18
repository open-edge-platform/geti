"""Result utils."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


def array_shape_to_str(array: np.ndarray | None) -> str:
    if array is not None:
        return f"[{','.join(str(i) for i in array.shape)}]"
    return "[]"
