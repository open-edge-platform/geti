# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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
    ROTATED_DETECTION = auto()  # ui project name is Detection Oriented
    CHAINED_DETECTION_CLASSIFICATION = auto()
    CHAINED_DETECTION_SEGMENTATION = auto()
    KEYPOINT_DETECTION = auto()
    UNKNOWN = auto()
