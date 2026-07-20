# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Standard-library logger for the ``getitrack`` package.

A ``NullHandler`` keeps the package silent until the application configures
logging or a tracker runs with ``verbose``. Records propagate to the root
logger so an application's own handlers and ``caplog`` see them.
"""

from __future__ import annotations

import logging
import sys

LOGGER = logging.getLogger("getitrack")
LOGGER.addHandler(logging.NullHandler())


def _has_console_handler() -> bool:
    """True if a handler already writes to stdout or stderr."""
    return any(getattr(handler, "stream", None) in (sys.stdout, sys.stderr) for handler in LOGGER.handlers)


def enable_logging(level: int = logging.INFO) -> None:
    """Set the package logger to ``level`` and attach a console handler if none exists.

    Idempotent, so repeated ``verbose`` construction adds at most one handler.
    """
    LOGGER.setLevel(level)
    if not _has_console_handler():
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
        LOGGER.addHandler(handler)
