# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import numpy as np
import pytest

from sc_sdk.entities.shapes import Rectangle
from tests.test_helpers import register_model_template


@pytest.mark.ScSdkComponent
class TestImage:
    def test_reading_image(self, request, fxt_random_annotated_image_factory) -> None:
        """
        <b>Description:</b>
        Check that an image can be read

        <b>Input data:</b>
        Randomly annotated project with an image

        <b>Expected results:</b>
        Test passes if the image can be read and a region of interest can be isolated from the frame

        <b>Steps</b>
        1. Create project with image
        2. Obtain image
        3. Read two ROI
        4. Read ROI with negative index
        5. Read ROI with out of bound indices
        """
        register_model_template(request, type(None), "detection", "DETECTION", trainable=True)
        image_numpy, _ = fxt_random_annotated_image_factory(image_width=100, image_height=200, labels=[])

        width = 100
        height = 200

        # Try to read a ROI
        subregion = Rectangle(0, 0, 10 / width, 15 / height).crop_numpy_array(image_numpy)
        np.testing.assert_equal(image_numpy[:15, :10], subregion)

        # Try to read another ROI
        subregion = Rectangle(2 / width, 3 / height, 10 / width, 15 / height).crop_numpy_array(image_numpy)
        np.testing.assert_equal(image_numpy[3:15, 2:10], subregion)

        # Try to read a ROI with a negative index
        # The indices should be clipped to the original image dimensions
        subregion = Rectangle(-5 / width, -10 / height, 10 / width, 15 / height).crop_numpy_array(image_numpy)
        np.testing.assert_equal(image_numpy[:15, :10], subregion)

        # Try to read a ROI with out of bound indices
        # The indices should be clipped to the original image dimensions
        subregion = Rectangle(5 / width, 10 / height, (width + 10) / width, (height + 15) / height).crop_numpy_array(
            image_numpy
        )
        np.testing.assert_equal(image_numpy[10:height, 5:width], subregion)
