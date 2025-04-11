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
from dataclasses import dataclass, fields


class DefaultFields:
    def __post_init__(self):
        """
        Substitutes fields with default value if None
        """
        for field in fields(self):
            if getattr(self, field.name) is None:
                setattr(self, field.name, field.default)


@dataclass
class POTOptimizationParameters(DefaultFields):
    """
    Store POT OptimizationParameters as an object.
    """

    stat_subset_size: int = 300
