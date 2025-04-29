# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Configuration file
"""

import os

GRPC_SERVICE_PORT = int(os.getenv("GRPC_SERVICE_PORT", "5555"))
MODELMESH_NAMESPACE = os.getenv("MODELMESH_NAMESPACE", "impt")
S3_BUCKETNAME = os.getenv("BUCKET_NAME_MODELMESH", "modelmesh")
S3_STORAGE = os.getenv("S3_STORAGE", "modelmesh")  # points to a name of ConfigMap with S3 storage config
RESOURCE_MS_SERVICE = os.getenv("RESOURCE_MS_SERVICE", "impt-resource")
RESOURCE_MS_PORT = os.getenv("RESOURCE_MS_PORT", "5000")
