# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Logging configuration and utilities for the application.

Provides centralized logging setup using loguru with:
- Console (stdout) and file-based logging sinks
- Configurable log levels, rotation (default: 10MB), and retention (default: 10 days)
- JSON serialization support for structured logging
- Thread-safe async logging with multiprocessing support
- Hypercorn log interception for unified application logging
"""

import logging
import multiprocessing
import os
import sys

from loguru import logger

from .config import LogConfig
from .handlers import InterceptHandler

context = multiprocessing.get_context("spawn")


def setup_logging(config: LogConfig | None = None) -> None:
    """Configure loguru logging with optional custom settings.

    Sets up loguru with stdout and file-based logging sinks. By default, creates
    a single log file with rotation and retention policies. Can be customized via
    LogConfig to specify different log levels, rotation sizes, and output locations.

    Args:
        config: Optional LogConfig instance. If None, uses default configuration
                with INFO level, 10MB rotation, and 10-day retention.

    Note:
        - Must be called in each child process separately, as loguru sinks don't
          transfer across process boundaries
        - BaseProcessWorker calls this automatically for worker processes
        - Call once at main process startup for application-level logging

    Example:
        >>> setup_logging()  # Uses defaults
        >>> custom_config = LogConfig(rotation="50 MB", level="DEBUG")
        >>> setup_logging(custom_config)
    """
    if config is None:
        config = LogConfig()

    logger.remove()

    logger.add(sys.stdout, level=config.level, colorize=True, enqueue=True, context=context)

    log_path = os.path.join(config.log_folder, config.log_file)
    try:
        logger.add(
            log_path,
            rotation=config.rotation,
            retention=config.retention,
            level=config.level,
            serialize=config.serialize,
            enqueue=True,
            context=context,
        )
    except Exception:
        logger.exception("Failed to add log sink for {}", log_path)


def setup_hypercorn_logging(log_level: str) -> None:
    """Configure hypercorn logging to be handled by loguru."""
    for logger_name in ("hypercorn.error", "hypercorn.access"):
        logger_ = logging.getLogger(logger_name)
        logger_.handlers = [InterceptHandler()]
        logger_.setLevel(log_level)
        logger_.propagate = False
