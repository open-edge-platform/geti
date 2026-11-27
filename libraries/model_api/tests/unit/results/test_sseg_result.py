#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import numpy as np
from model_api.models.result import Contour


def test_contour_type():
    contour = Contour(
        shape=[(100, 100)],
        label=1,
        probability=0.9,
        excluded_shapes=[[(50, 50)], [(60, 60)]],
    )

    assert isinstance(contour.shape, np.ndarray)
    assert isinstance(contour.excluded_shapes, list)
    assert isinstance(contour.excluded_shapes[0], np.ndarray)
    assert contour.label == 1
    assert contour.probability == 0.9
    assert np.array_equal(contour.excluded_shapes, np.array([[(50, 50)], [(60, 60)]]))
