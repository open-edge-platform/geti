# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import os

from constants.paths import DATA_FOLDER
from texts.validators import PathValidatorsTexts
from validators.errors import ValidationError


def create_default_data_folder() -> None:
    """
    This function creates a directory with the specified path and sets its permissions to 750.
    Raises ValidationError if the directory already exists or if there are permission issues.
    """
    try:
        os.makedirs(DATA_FOLDER, mode=0o750)
    except FileExistsError:
        raise ValidationError(PathValidatorsTexts.path_already_exists.format(path=DATA_FOLDER))
    except PermissionError:
        raise ValidationError(PathValidatorsTexts.path_permission_error.format(path=DATA_FOLDER))
