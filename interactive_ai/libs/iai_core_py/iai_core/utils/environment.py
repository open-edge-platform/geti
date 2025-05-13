# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
