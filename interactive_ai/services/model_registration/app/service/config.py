# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

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
