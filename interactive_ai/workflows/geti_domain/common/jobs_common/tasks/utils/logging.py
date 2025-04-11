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

"""This module defines methods and wrappers to initialize logger for tasks"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from geti_logger_tools.logger_config import initialize_logger
from geti_telemetry_tools.tracing.common import get_logging_format_with_tracing_context
from geti_types import SESSION_LOGGING_FORMAT_HEADER, enhance_log_records_with_session_info


def init_logger(package_name: Any) -> Any:
    """
    Decorator to initialize logger
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Callable:
            start_common_logger(package_name=package_name, use_async=False)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def start_common_logger(package_name: str | None = None, use_async: bool = False) -> logging.Logger:
    """
    Initialize common_logger and disable/reconfigure external loggers
    that may interfere with it

    :param package_name: name of the package for which the logger should be started
    :param use_async: bool indicating whether to use async
    """
    if package_name is None:
        package_name = __name__
    logging_format = get_logging_format_with_tracing_context(extra_headers=SESSION_LOGGING_FORMAT_HEADER)
    logger = initialize_logger(package_name, use_async=use_async, logging_format=logging_format)
    enhance_log_records_with_session_info()

    return logger
