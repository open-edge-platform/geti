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

"""This module contains the keys that can be used to retrieve parameter metadata."""

DEFAULT_VALUE = "default_value"
MIN_VALUE = "min_value"
MAX_VALUE = "max_value"
STEP_SIZE = "step_size"
DESCRIPTION = "description"
HEADER = "header"
WARNING = "warning"
EDITABLE = "editable"
VISIBLE_IN_UI = "visible_in_ui"
AFFECTS_OUTCOME_OF = "affects_outcome_of"
UI_RULES = "ui_rules"
TYPE = "type"
OPTIONS = "options"
ENUM_NAME = "enum_name"
AUTO_HPO_STATE = "auto_hpo_state"  # legacy; kept for backward-compatibility
AUTO_HPO_VALUE = "auto_hpo_value"  # legacy; kept for backward-compatibility


def allows_model_template_override(keyword: str) -> bool:
    """Returns True if the metadata element described by `keyword` can be overridden in a model template file.

    :param keyword: Name of the metadata key to check.
    :return: True if the metadata indicated by `keyword` can be overridden in a model template .yaml file, False
        otherwise.
    """
    overrideable_keys = [
        DEFAULT_VALUE,
        MIN_VALUE,
        MAX_VALUE,
        DESCRIPTION,
        HEADER,
        EDITABLE,
        WARNING,
        VISIBLE_IN_UI,
        OPTIONS,
        ENUM_NAME,
        UI_RULES,
        AFFECTS_OUTCOME_OF,
        AUTO_HPO_STATE,
    ]
    return keyword in overrideable_keys


def allows_dictionary_values(keyword: str) -> bool:
    """Returns True if the metadata element described by `keyword` allows having a dictionary as its value.

    :param keyword: Name of the metadata key to check.
    :return: True if the metadata indicated by `keyword` allows having a dictionary as its value, False otherwise.
    """
    keys_allowing_dictionary_values = [OPTIONS, UI_RULES]
    return keyword in keys_allowing_dictionary_values


def all_keys() -> list[str]:
    """Returns a list of all metadata keys."""
    return [
        DEFAULT_VALUE,
        MIN_VALUE,
        MAX_VALUE,
        DESCRIPTION,
        HEADER,
        WARNING,
        EDITABLE,
        VISIBLE_IN_UI,
        AFFECTS_OUTCOME_OF,
        UI_RULES,
        TYPE,
        OPTIONS,
        ENUM_NAME,
        AUTO_HPO_STATE,
        AUTO_HPO_VALUE,
    ]


def deprecated_keys() -> list[str]:
    """Returns a list of deprecated metadata keys."""
    return [AUTO_HPO_STATE, AUTO_HPO_VALUE]
