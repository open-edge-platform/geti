# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
