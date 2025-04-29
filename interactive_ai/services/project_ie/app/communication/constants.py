# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements constants
"""

import os

try:
    MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION: int | None = int(os.environ.get("MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION"))  # type: ignore[arg-type]
except (ValueError, TypeError):
    MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION = None
