# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os

from geti_logger_tools.logger_config import initialize_logger

logger = initialize_logger(__name__, use_async=False)

os.environ["ENABLE_TRACING"] = "true"
os.environ["DEBUG_TRACES"] = "true"
os.environ["TEST_METRICS"] = "true"
