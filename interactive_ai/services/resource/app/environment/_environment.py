# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

logger = logging.getLogger(__name__)

_ENV_GRAFANA_ENABLED = "GRAFANA_ENABLED"
_ENV_ENVIRONMENT = "ENVIRONMENT"
_ENV_GPU_PROVIDER = "GPU_PROVIDER"


def get_gpu_provider() -> str:
    val = os.environ.get(_ENV_GPU_PROVIDER, "")
    if "intel" in val:
        gpu_provider = "intel"
    elif "nvidia" in val:
        gpu_provider = "nvidia"
    else:
        gpu_provider = "none"
    return gpu_provider


def get_environment() -> str:
    """
    Returns environment type identifier (saas/on-prem).
    """
    val = os.getenv(_ENV_ENVIRONMENT)
    if val is None:
        logger.warning(f"Environment variable {_ENV_ENVIRONMENT} is not defined. Assuming environment is on-prem.")
        return "on-prem"

    return val


def is_grafana_enabled() -> bool:
    """
    Returns status of Grafana enablement.
    """
    try:
        val = os.environ[_ENV_GRAFANA_ENABLED]
        return val.lower() == "true"
    except KeyError:
        logger.warning(f"Environment variable {_ENV_GRAFANA_ENABLED} is not defined. Assuming Grafana is disabled.")
        return False
