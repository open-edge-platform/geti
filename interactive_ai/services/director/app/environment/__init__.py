# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os

_ENV_GPU_PROVIDER = "GPU_PROVIDER"


def get_gpu_provider() -> str:
    """Returns the GPU provider based on the environment variable GPU_PROVIDER."""
    val = os.environ.get(_ENV_GPU_PROVIDER, "")
    if "intel" in val:
        gpu_provider = "intel"
    elif "nvidia" in val:
        gpu_provider = "nvidia"
    else:
        gpu_provider = "none"
    return gpu_provider
