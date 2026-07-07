# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Standard-library logger for the ``getitrack`` package.

A ``NullHandler`` keeps the package silent until the application configures
logging or a tracker runs with ``verbose``.
"""

from __future__ import annotations

import logging

LOGGER = logging.getLogger("getitrack")
LOGGER.addHandler(logging.NullHandler())


def enable_logging(level: int = logging.INFO) -> None:
    """Set the logger to ``level`` and attach a console handler if none exists.

    Idempotent, so repeated ``verbose`` construction adds at most one handler.
    """
    LOGGER.setLevel(level)
    if not any(isinstance(handler, logging.StreamHandler) for handler in LOGGER.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        LOGGER.addHandler(handler)
