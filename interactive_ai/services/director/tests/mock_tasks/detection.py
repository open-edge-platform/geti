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

import logging

from pytest import FixtureRequest

from tests.test_helpers import register_model_template

from sc_sdk.entities.model_template import ModelTemplate

logger = logging.getLogger(__name__)


class ObjectDetection:
    """
    Mock detection task
    """


def register_detection_task(test_case: FixtureRequest) -> ModelTemplate:
    """Register ObjectDetection task to model template list"""
    return register_model_template(
        test_case,
        ObjectDetection,
        "mock/ObjectDetection",
        "DETECTION",
        trainable=True,
    )
