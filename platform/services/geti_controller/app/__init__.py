# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from geti_types import SESSION_LOGGING_FORMAT_HEADER

import rest
from geti_logger_tools.logger_config import initialize_logger
from geti_telemetry_tools.tracing.common import get_logging_format_with_tracing_context

__all__ = ["rest"]

logging_format = get_logging_format_with_tracing_context(extra_headers=SESSION_LOGGING_FORMAT_HEADER)
logger = initialize_logger(__name__, use_async=False, logging_format=logging_format)
logger.info("Logger has been initialized in the Geti Controller microservice.")
