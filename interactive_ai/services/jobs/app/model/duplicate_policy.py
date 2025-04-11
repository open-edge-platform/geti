# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
Duplicate policy module
"""

from enum import Enum, auto


class DuplicatePolicy(Enum):
    """
    Duplicate policy enumeration
    Represents possible duplicate policies

    REPLACE             Duplicate job with SUBMITTED state is marked as cancelled and new is submitted instead.
    OMIT                Job is not to be submitted if duplicate job exist in a pre-running state
    REJECT              Job is not to be submitted and error is returned if duplicate job exist in a pre-running state
    """

    REPLACE = auto()
    OMIT = auto()
    REJECT = auto()
