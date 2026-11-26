#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import numpy as np
from model_api.models.result import DetectionResult


def test_cls_result():
    tst_vector = np.array([1, 2, 3, 4], dtype=np.float32)
    det_result = DetectionResult(
        tst_vector,
        tst_vector,
        tst_vector,
        ["a"],
        tst_vector,
        tst_vector,
    )

    assert det_result.labels.dtype == np.int32
    assert len(det_result.label_names) == 1
