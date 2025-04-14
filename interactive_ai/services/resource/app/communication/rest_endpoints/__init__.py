# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from .annotation_endpoints import annotation_router
from .code_deployment_endpoints import code_deployment_router, deployment_package_router
from .dataset_endpoints import dataset_router
from .media_endpoints import media_router
from .media_score_endpoints import media_score_router
from .model_endpoints import model_router
from .product_info_endpoints import product_info_router
from .project_endpoints import project_router
from .status_endpoints import status_router
from .user_settings_endpoints import server_router
from .workspace_endpoints import workspace_router

__all__ = [
    "annotation_router",
    "code_deployment_router",
    "dataset_router",
    "deployment_package_router",
    "media_router",
    "media_score_router",
    "model_router",
    "product_info_router",
    "project_router",
    "server_router",
    "status_router",
    "workspace_router",
]
