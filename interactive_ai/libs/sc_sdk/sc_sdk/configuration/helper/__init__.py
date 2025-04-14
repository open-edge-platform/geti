# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
