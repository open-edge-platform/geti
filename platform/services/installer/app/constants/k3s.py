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
"""Module containing constants related to k3s installation/upgrade"""

# If this constant is set to True, K3S will be upgraded during upgrade operation
UPGRADE_K3S = True

# Minimal available free disk space threshold, for k3s pod eviction, in Gi units
MIN_FREE_DISK_SPACE_GIB = 5
