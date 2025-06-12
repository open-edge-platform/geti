# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

from fastapi import HTTPException, status

from platform_operations.cluster.cluster import (
    check_config_map_exists,
    create_cluster_role,
    create_cluster_role_binding,
    create_job,
    create_service_account,
    deploy_cluster_role,
    deploy_cluster_role_binding,
    deploy_job,
    deploy_service_account,
    load_kube_config,
)
from rest.schema.install import InstallRequest, InstallResponse
from routers import platform_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@platform_router.post(
    path="/install",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Installation process started successfully.",
            "content": {
                "application/json": {"example": InstallResponse(detail="Installation of version 2.9.0 has started.")}
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid request or installation cannot be started.",
            "content": {"application/json": {"example": {"detail": "Version number is required."}}},
        },
        status.HTTP_409_CONFLICT: {
            "description": "Platform is already installed or conflicting state detected.",
            "content": {"application/json": {"example": {"detail": "Platform is already installed."}}},
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected error occurred while starting the installation process.",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to start the installation process due to an internal error."}
                }
            },
        },
    },
)
def install_platform(payload: InstallRequest) -> InstallResponse:
    """
    Starts the installation of the specified platform version.
    """
    logger.debug(f"POST install request received. Payload: {payload}")

    if not payload.version_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Version number is required.",
        )

    if payload.version_number == "invalid_version":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid version number provided.",
        )

    load_kube_config()
    if check_config_map_exists(name="impt-configuration", namespace="impt"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Platform is already installed.")

    sa = create_service_account(name="install-upgrade", namespace="default")
    cr = create_cluster_role(name="install-upgrade")
    crb = create_cluster_role_binding(
        name="install-upgrade", service_account_name="install-upgrade", namespace="default"
    )
    deploy_service_account(sa, namespace="default")
    deploy_cluster_role(cr)
    deploy_cluster_role_binding(crb)
    # TODO change tag to generated one
    job = create_job(
        name="install-upgrade",
        registry=f"{os.environ.get('REGISTRY')}/open-edge-platform",
        image=f"{os.environ.get('REGISTRY')}/open-edge-platform/geti/install-upgrade:2.11.0-test-20250612140230",
        manifest_version=os.environ.get("VERSION"),
    )
    deploy_job(job, namespace="default")

    logger.info(f"Installation of version {payload.version_number} has started.")
    return InstallResponse(detail=f"Installation of version {payload.version_number} has started.")
