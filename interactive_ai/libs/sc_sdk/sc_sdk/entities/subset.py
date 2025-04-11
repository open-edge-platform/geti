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

"""This file defines the Subset enum for use in datasets."""

from enum import Enum


class Subset(Enum):
    """Describes the Subset a DatasetItem is assigned to."""

    NONE = 0
    TRAINING = 1
    VALIDATION = 2
    TESTING = 3
    UNLABELED = 4
    PSEUDOLABELED = 5
    UNASSIGNED = 6

    def __str__(self):
        """Returns name of subset."""
        return str(self.name)

    def __repr__(self):
        """Returns name of subset."""
        return f"Subset.{self.name}"
