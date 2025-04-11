# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

import os

from geti_logger_tools.logger_config import initialize_logger

logger = initialize_logger(__name__, use_async=False)

os.environ["ENABLE_TRACING"] = "true"
os.environ["DEBUG_TRACES"] = "true"
os.environ["TEST_METRICS"] = "true"
