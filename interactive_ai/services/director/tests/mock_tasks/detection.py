# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from pytest import FixtureRequest

from tests.test_helpers import register_model_template

from iai_core_py.entities.model_template import ModelTemplate

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
