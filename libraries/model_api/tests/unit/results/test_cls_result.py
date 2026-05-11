#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import numpy as np
from model_api.models.result import ClassificationResult, Label


def test_cls_result():
    label = Label(1, "label", 0.5)
    tst_vector = np.array([1, 2, 3])
    cls_result = ClassificationResult([label], tst_vector, tst_vector, tst_vector)

    assert cls_result.top_labels[0].id == 1
    assert cls_result.top_labels[0].name == "label"
    assert cls_result.top_labels[0].confidence == 0.5
    assert str(cls_result) == "1 (label): 0.500, [3], [3], [3]"
    assert cls_result.top_labels[0].__str__() == "1 (label): 0.500"
    assert tuple(cls_result.top_labels[0].__iter__()) == (1, "label", 0.5)
