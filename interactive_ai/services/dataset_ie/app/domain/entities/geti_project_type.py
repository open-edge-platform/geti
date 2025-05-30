# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module define enums and constants"""

from enum import Enum, auto


class GetiProjectType(Enum):
    """Enum for Geti project type"""

    CLASSIFICATION = auto()
    HIERARCHICAL_CLASSIFICATION = auto()
    DETECTION = auto()
    SEGMENTATION = auto()
    INSTANCE_SEGMENTATION = auto()
    ANOMALY_CLASSIFICATION = auto()
    ANOMALY_DETECTION = auto()
    ANOMALY_SEGMENTATION = auto()
    ANOMALY = auto()
    ROTATED_DETECTION = auto()  # ui project name is Detection Oriented
    CHAINED_DETECTION_CLASSIFICATION = auto()
    CHAINED_DETECTION_SEGMENTATION = auto()
    KEYPOINT_DETECTION = auto()
    UNKNOWN = auto()
