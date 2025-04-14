# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Director microservice"""

import logging

from geti_logger_tools.logger_config import initialize_logger

from geti_telemetry_tools import ENABLE_TRACING, LoggerTelemetry
from geti_telemetry_tools.tracing.common import get_logging_format_with_tracing_context
from geti_types import SESSION_LOGGING_FORMAT_HEADER, enhance_log_records_with_session_info


def configure_logger() -> logging.Logger:
    """
    Initialize and configures logger, disable/reconfigure external loggers
    that may interfere with it
    """
    # Get the logging format; if tracing is enabled, the format should include the trace/span ids too
    logging_format = get_logging_format_with_tracing_context(extra_headers=SESSION_LOGGING_FORMAT_HEADER)

    # Setup the base logger; immediately after enhance the log records with session
    # and tracing information, as strictly required by the logging format
    logger = initialize_logger(__name__, use_async=False, logging_format=logging_format)
    if ENABLE_TRACING:
        LoggerTelemetry.instrument()
    enhance_log_records_with_session_info()
    logger.debug("Initialized logger with format: '%s'", logging_format)

    # Apply special configuration to some external loggers
    logging.getLogger("werkzeug").disabled = True
    logging.getLogger("pika").setLevel(logging.WARNING)

    for logger_name in ["uvicorn.access", "uvicorn"]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.propagate = True
        for handler in uvicorn_logger.handlers:
            uvicorn_logger.removeHandler(handler)

    return logger


# By running this code in __init__.py, we make sure that logging is properly initialized
# as soon as the microservice is loaded, before loading other modules.
logger = configure_logger()
logger.info("Logger has been initialized in the Director MS")
