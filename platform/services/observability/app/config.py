# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Configuration file
"""

import os

LOGS_DIR = os.getenv("LOGS_DIR", "/logs")
IMPT_CONFIGURATION_CM = os.getenv("IMPT_CONFIGURATION_CM", "impt-configuration")
K8S_CR_NAMESPACE = os.getenv("K8S_CR_NAMESPACE", "default")

USE_KUBECONFIG = os.getenv("USE_KUBECONFIG", "False").lower() == "true"

IMPT_RESOURCE_SERVICE_HOST = os.getenv("IMPT_RESOURCE_SERVICE_HOST", "10.0.0.0")
IMPT_RESOURCE_SERVICE_PORT = int(os.getenv("IMPT_RESOURCE_SERVICE_PORT", "5000"))
