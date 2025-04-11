# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
init module for logs directory
"""

import logging

from .logs import logs_endpoint
from .router import logs_router

logger = logging.getLogger(__name__)


__all__ = ["logs_endpoint", "logs_router"]
