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

"""This module contains the configuration helper functions.

These can be used to create, convert or interact with OTX configuration objects or dictionaries, yaml strings or yaml
files representing those objects.
"""

from .convert import convert
from .create import create
from .substitute import substitute_values, substitute_values_for_lifecycle
from .utils import config_to_bytes, flatten_config_values, merge_a_into_b
from .validate import validate

__all__ = [
    "config_to_bytes",
    "convert",
    "create",
    "flatten_config_values",
    "merge_a_into_b",
    "substitute_values",
    "substitute_values_for_lifecycle",
    "validate",
]
