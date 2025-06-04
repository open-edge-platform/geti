# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
"""Module containing other common variables used in the platform installer"""

import os

PLATFORM_NAMESPACE = "impt"

PLATFORM_CONFIGURATION_CM_NAME = f"{PLATFORM_NAMESPACE}-configuration"
PLATFORM_VERSION_CM_KEY = "platformVersion"

DATA_DIRS_REMOVAL_REQUIRED = ["mongodb", "ldap", "ldap-config"]
DATA_STORAGE_VOLUME_NAME = "data-storage-volume"
DATA_STORAGE_VOLUME_CLAIM_NAME = f"{DATA_STORAGE_VOLUME_NAME}-claim"

INTERNAL_REGISTRY_ADDRESS = "127.0.0.1:30000"
PLATFORM_REGISTRY_ADDRESS = os.getenv("PLATFORM_REGISTRY_ADDRESS", "")
EXTERNAL_REGISTRY_ADDRESS = os.getenv("EXTERNAL_REGISTRY_ADDRESS", "")
INTEL_EMAIL = "Geti.Team@intel.com"

GPU_PROVIDER_NVIDIA = "nvidia"
GPU_PROVIDER_INTEL_MAX = "intel-max"
GPU_PROVIDER_INTEL_ARC = "intel-arc"
GPU_PROVIDER_INTEL_ARC_A = "intel-arc-a"

DEFAULT_HISTORY_MAX = 3

DEFAULT_USERNAME = "admin@geti.com"
