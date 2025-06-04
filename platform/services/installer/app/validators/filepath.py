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
A module with validating functions for files
"""

import re
from os import R_OK, access
from os.path import isfile

from click import BadParameter, Context, Parameter

from texts.validators import FilepathValidatorsTexts
from validators.errors import ValidationError


def is_filepath_valid(context: Context, param: Parameter, filepath: str) -> str:  # noqa: ARG001
    """
    Validates filepath, raises ValidationError if given filepath is invalid

    context: Click context object
    param: Click parameter object
    filepath: Value of the parameter
    """
    try:
        if not filepath:
            return ""
        regex = re.compile(r"(^[\/].*$)")
        if not re.fullmatch(regex, str(filepath)):
            raise ValidationError(FilepathValidatorsTexts.invalid_filepath.format(filepath=filepath))
        if not isfile(filepath):
            raise ValidationError(FilepathValidatorsTexts.filepath_not_exists.format(filepath=filepath))
        if not access(filepath, R_OK):
            raise ValidationError(FilepathValidatorsTexts.filepath_not_readable.format(filepath=filepath))
    except ValidationError as e:
        raise BadParameter(str(e))
    return filepath
