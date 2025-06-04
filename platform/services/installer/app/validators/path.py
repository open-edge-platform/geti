# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
A module with validating functions for data folder path.
"""

import os.path
import re

from click import BadParameter, Context, Parameter

from constants.paths import DATA_FOLDER
from platform_utils.path import create_default_data_folder
from texts.validators import PathValidatorsTexts
from validators.errors import ValidationError


def is_path_valid(path: str):  # noqa: ANN201
    """
    Checks whether the path is absolute, is not empty, is a not a directory and does not exist.
    Raises ValidationError if given path is invalid.
    """
    regex = re.compile(r"(^[\/].*$)")
    if not re.fullmatch(regex, str(path)):
        raise ValidationError(PathValidatorsTexts.invalid_path.format(path=path, folder=DATA_FOLDER))
    if not os.path.exists(path):
        raise ValidationError(PathValidatorsTexts.path_not_exists.format(path=path, folder=DATA_FOLDER))
    if os.path.isfile(path):
        raise ValidationError(PathValidatorsTexts.path_not_folder.format(path=path))
    if os.listdir(path):
        raise ValidationError(PathValidatorsTexts.path_not_empty.format(path=path))


def is_data_folder_valid(context: Context, param: Parameter, value: str) -> str:  # noqa: ARG001
    """
    Validates data folder path in terms of permissions.
    If directory is not provided, it creates a default data folder.
    Raises ValidationError if given path has incorrect permissions.

    context: Click context object
    param: Click parameter object
    value: Value of the parameter
    """
    try:
        if not value:
            create_default_data_folder()
        else:
            is_path_valid(value)
            if get_path_permissions(value)[-1] != "0":
                raise ValidationError(
                    PathValidatorsTexts.invalid_permissions.format(path=value, permissions=get_path_permissions(value))
                )
    except ValidationError as e:
        raise BadParameter(str(e))
    return value if value else DATA_FOLDER


def get_path_permissions(path: str) -> str:
    """
    Extracts permissions of file or directory of given path.
    """
    path_metadata = os.stat(path=path)
    permissions_code = oct(path_metadata.st_mode)[-3:]
    return str(permissions_code)
