# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
import logging

import cv2
import numpy as np
from sc_sdk.entities.model import Model, TrainingFrameworkType

logger = logging.getLogger(__name__)


def downscale_image(image: np.ndarray, target_largest_size: int) -> np.ndarray:
    """
    Downscale the image while maintaining the aspect ratio. If the image is already smaller than the target size,
    no resizing is performed.

    :param image: input image
    :param target_largest_size: target size for the largest dimension
    :return: downscaled image
    """
    og_height, og_width = image.shape[:2]
    # resize the largest dimension to RESIZED_IMAGE_SIZE while maintaining the aspect ratio
    if og_height > og_width:
        new_height = target_largest_size
        new_width = int(new_height / og_height * og_width)
    else:
        new_width = target_largest_size
        new_height = int(new_width / og_width * og_height)
    if og_height * og_width > new_height * new_width:
        # AREA interpolation works best when downscaling:
        # https://web.archive.org/web/20190424180810/http://tanbakuchi.com/posts/comparison-of-openv-interpolation-algorithms/
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    # no resize needed, as it is already smaller than the target size
    return image


def is_model_legacy_otx_version(model: Model) -> bool:
    """
    Checks if the model is a legacy OTX version (< 2.0)

    :param model: the model to check
    """
    return (
        model.training_framework.type == TrainingFrameworkType.OTX
        and int(model.training_framework.version.split(".")[0]) < 2
    )
