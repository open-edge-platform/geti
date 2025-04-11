# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

"""Utilities relative to OS and environment"""

import os
from collections.abc import Sequence


def check_required_env_vars(required_variables: Sequence[str]) -> None:
    """
    Check if the given environment variables are set.

    :param required_variables: A sequence of strings containing the names of the required environment variables.
    :raises ValueError: If one or more environment variables are missing.
    """
    missing_env_variables = set(required_variables) - set(os.environ)
    if missing_env_variables:
        missing_variables_str = ", ".join(missing_env_variables)
        raise ValueError(f"Required environment variable(s) {missing_variables_str} are not set.")
