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

"""This module contains utility functions used within the configuration helper module."""

import copy
import json
import os
from enum import Enum
from typing import Any

import yaml
from omegaconf import DictConfig, OmegaConf

from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.enums.utils import get_enum_names

from .config_element_mapping import GroupElementMapping, PrimitiveElementMapping, RuleElementMapping
from .convert import convert
from geti_types import ID


def _search_in_config_dict_inner(
    config_dict: dict,
    key_to_search: str,
    prior_keys: list[str] | None = None,
    results: list[tuple[Any, list[str]]] | None = None,
) -> list[tuple[Any, list[str]]]:
    """Helper function for the `search_in_config_dict` function defined below.

    :param config_dict: dict to search in
    :param key_to_search: dict key to look for
    :param prior_keys: List of prior keys leading to the key_to_search.
    :param results: List of previously found results
    :return: List of (value_at_key_to_search, key_path_to_key_to_search) tuples, representing each occurrence of
        key_to_search within config_dict
    """
    if prior_keys is None:
        prior_keys = []
    if results is None:
        results = []
    if isinstance(config_dict, list):
        dict_to_search_in = dict(zip(range(len(config_dict)), config_dict))
    else:
        dict_to_search_in = config_dict
    if not (issubclass(type(dict_to_search_in), dict) or isinstance(dict_to_search_in, DictConfig)):
        return results
    for key, value in dict_to_search_in.items():
        current_key_path = [*prior_keys, key]
        if key == key_to_search:
            results.append((value, prior_keys))
        _search_in_config_dict_inner(value, key_to_search, current_key_path, results)
    return results


def search_in_config_dict(config_dict: dict, key_to_search: str) -> list[tuple[Any, list[str]]]:
    """Recursively searches a config_dict for all instances of key_to_search and returns the key path to them.

    :param config_dict: dict to search in
    :param key_to_search: dict key to look for
    :return: List of (value_at_key_to_search, key_path_to_key_to_search) tuples, representing each occurrence of
        key_to_search within config_dict
    """
    return _search_in_config_dict_inner(config_dict, key_to_search=key_to_search)


def input_to_config_dict(input_config: str | DictConfig | dict, check_config_type: bool = True) -> dict:
    """Validate input configuration.

    Takes an input_config which can be a string, filepath, dict or DictConfig and performs basic validation that it
    can be converted into a configuration.

    :param input_config: String, filepath, dict or DictConfig describing a configuration
    :param check_config_type: True to check that the input has a proper `type` attribute in order to be converted into
        a ConfigurableParameters object. False to disable this check. Defaults to True
    :return: dictionary or DictConfig
    """
    valid_types = (
        get_enum_names(PrimitiveElementMapping)
        + get_enum_names(RuleElementMapping)
        + get_enum_names(GroupElementMapping)
    )

    if isinstance(input_config, str):
        if os.path.exists(input_config):
            with open(input_config, encoding="UTF-8") as file:
                result = yaml.safe_load(file)
        else:
            result = yaml.safe_load(input_config)
    elif issubclass(type(input_config), dict):
        result = input_config
    elif isinstance(input_config, DictConfig):
        result = OmegaConf.to_container(input_config)
    else:
        raise ValueError('Invalid input_config type! Valid types are "str", "DictConfig", "dict".')

    if check_config_type:
        config_type = str(result.get("type", None))

        if config_type is None:
            raise ValueError(
                f"Input cannot be converted to a valid configuration. No "
                f"configuration type was found in the following input: {input_config}"
            )
        if config_type not in valid_types:
            raise ValueError(
                f"Invalid configuration element type: {config_type} found in input. "
                f"Unable to parse input. Supported configuration element types are:"
                f" {valid_types}"
            )
    return result


def deserialize_enum_value(value: str | Enum, enum_type: type[Enum]) -> Enum:
    """Deserializes a value to an instance of a certain Enum.

    This checks whether the `value` passed is already an instance of the target Enum, in which case this function just
    returns the input `value`. If value is a string, this function returns the corresponding instance of the Enum
    passed in `enum_type`.

    :param value: value to deserialize
    :param enum_type: class (should be a subclass of Enum) that the name belongs to
    :return: instance of `enum_type`.`value`
    """
    if isinstance(value, enum_type):
        instance = value
    elif isinstance(value, str):
        try:
            instance = enum_type[value.upper()]
        except KeyError:
            try:
                instance = enum_type(value)  # type: ignore
            except ValueError as error:
                raise KeyError(f"Value `{value}` cannot be converted to an instance of `{enum_type}`") from error
    else:
        raise ValueError(f"Invalid input data type, {type(value)} cannot be converted to an instance of {enum_type}.")
    return instance


def ids_to_strings(config_dict: dict) -> dict:
    """Converts ID's in the `config_dict` to their string representation.

    :param config_dict: Dictionary in which to replace the ID's by strings
    :return: Updated config_dict dictionary
    """
    for key, value in config_dict.items():
        if isinstance(value, ID):
            config_dict[key] = str(value)
    return config_dict


def config_to_bytes(config: ConfigurableParameters) -> bytes:
    """Converts ConfigurableParameters to bytes.

    :param config: configurable parameters
    :return: JSON in bytes
    """
    config_dict = convert(config, dict, enum_to_str=True)
    return json.dumps(config_dict, indent=4).encode()


def flatten_config_values(config: dict) -> None:
    """Extracts the "value" field from any nested config.

    Flattening the structure of the config dictionary. The original config dictionary is modified in-place.

    :param config: config dictionary
    """
    for key, value in config.items():
        if isinstance(value, dict):
            if "value" in value:
                config[key] = value["value"]
            else:
                flatten_config_values(value)


def flatten_detection_config_groups(config: dict) -> None:
    """Converts all Detection Config Group objects in a config dictionary to their dictionary representation.

    :param config: config dictionary
    """
    for key, value in config.items():
        if hasattr(value, "__dict__"):
            config[key] = value.__dict__
        elif isinstance(value, dict):
            flatten_detection_config_groups(value)


def merge_a_into_b(dict_a: dict, dict_b: dict) -> dict:
    """Inspired by mmcv.Config.merge_a_into_b by merging dict ``a`` into dict ``b`` (non-inplace).

    Values in ``a`` will overwrite ``b``. ``b`` is copied first to avoid
    in-place modifications.

    Examples:
        # Normally merge a into b.
        >>> merge_a_into_b({'a': {'d': 5, 'e': 6}, 'b': 4}, {'a': {'c': 1, 'd': 4}, 'b': 3})
        {'a': {'c': 1, 'd': 5, 'e': 6}, 'b': 4}

    :param dict_a: The source dict to be merged into ``b``.
    :param dict_b: The origin dict to be fetch keys from ``a``.
    :return: The modified dict of ``b`` using ``a``.
    """
    dict_b = copy.deepcopy(dict_b)
    for key, value in dict_a.items():
        if isinstance(value, dict):
            if key in dict_b:
                dict_b[key] = merge_a_into_b(value, dict_b[key])
            else:
                dict_b[key] = value
        else:
            dict_b[key] = value
    return dict_b
