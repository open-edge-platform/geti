# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

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
