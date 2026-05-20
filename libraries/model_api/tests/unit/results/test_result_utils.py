# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from model_api.models.result.utils import array_shape_to_str


def test_array_shape_to_str_with_array():
    arr = np.zeros((3, 4, 5))
    assert array_shape_to_str(arr) == "[3,4,5]"


def test_array_shape_to_str_with_1d():
    arr = np.zeros((10,))
    assert array_shape_to_str(arr) == "[10]"


def test_array_shape_to_str_with_none():
    assert array_shape_to_str(None) == "[]"
