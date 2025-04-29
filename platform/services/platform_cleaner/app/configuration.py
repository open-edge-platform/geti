"""Module for storing platform's workloads auto removal configuration"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from pathlib import Path

# General configuration
PATH_LOGS_DIR = Path(os.environ.get("PATH_LOGS_DIR", "/mnt/logs"))

PLATFORM_NAMESPACE = os.environ.get("PLATFORM_NAMESPACE", "impt")

ENABLE_TELEMETRY_CLEANUP = os.environ.get("ENABLE_TELEMETRY_CLEANUP", "TRUE")

NAMESPACES = (PLATFORM_NAMESPACE,)

# Inference services cleanup

INFERENCE_SERVICE_AGE_THRESHOLD_HOURS = int(os.environ.get("INFERENCE_SERVICE_AGE_THRESHOLD_HOURS ", "48"))
