# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

from dataclasses import dataclass


@dataclass
class VideoAnnotationProperties:
    """
    Stores the video annotation properties for the rest view
    """

    total_count: int
    total_requested_count: int
    start_frame: int | None = None
    end_frame: int | None = None
    requested_start_frame: int | None = None
    requested_end_frame: int | None = None
