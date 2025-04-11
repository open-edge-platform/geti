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

"""This module implements the VideoAnnotationStatistics entity"""

from dataclasses import dataclass


@dataclass
class VideoAnnotationStatistics:
    """
    VideoAnnotationStatistics stores the number of annotated, partially annotated and unannotated frames of a video
    """

    annotated: int
    unannotated: int
    partially_annotated: int
