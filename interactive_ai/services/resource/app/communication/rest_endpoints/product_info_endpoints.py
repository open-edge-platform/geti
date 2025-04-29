# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

from fastapi import APIRouter

from environment import get_environment, get_gpu_provider, is_grafana_enabled

logger = logging.getLogger(__name__)

product_info_router = APIRouter(prefix="/api/v1", tags=["Product Info"])


@product_info_router.get("/product_info")
def get_product_info_endpoint() -> dict[str, str | bool]:
    """
    Endpoint to retrieve product info data
    """
    platform_version = str(os.getenv("PLATFORM_VERSION"))
    build_version = str(os.getenv("BUILD_VERSION"))
    intel_email = str(os.getenv("INTEL_EMAIL"))

    smtp_defined = "False"
    try:
        with open("/mnt/smtp_server_secret/smtp_host") as file:
            smtp_host = file.read()
            if smtp_host:
                smtp_defined = "True"
    except FileNotFoundError:
        pass

    return {
        "product-version": platform_version,
        "build-version": build_version,
        "smtp-defined": smtp_defined,
        "intel-email": intel_email,
        "grafana_enabled": is_grafana_enabled(),
        "environment": get_environment(),
        "gpu-provider": get_gpu_provider(),
    }
