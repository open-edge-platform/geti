# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import numpy as np

from iai_core_py.entities.shapes import Rectangle
from tests.test_helpers import register_model_template


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
