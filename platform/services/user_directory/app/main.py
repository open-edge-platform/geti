# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import sys

import endpoints.user_management
import sherlock
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from geti_logger_tools.logger_config import initialize_logger
from geti_telemetry_tools import ENABLE_TRACING, FastAPITelemetry, LoggerTelemetry
from geti_telemetry_tools.tracing.common import get_logging_format_with_tracing_context
from service_connection.k8s_client.apis import K8S

from common.endpoint_validation import handle_request_validation_error

app = FastAPI()
logging_format = get_logging_format_with_tracing_context()
logger = initialize_logger(__name__, logging_format=logging_format)
if ENABLE_TRACING:
    LoggerTelemetry.instrument()

if "pytest" in sys.modules:
    logger.warning("Running inside a pytest session. Skipping sherlock configuration.")
else:
    sherlock.configure(
        backend=sherlock.backends.KUBERNETES, expire=None, retry_interval=0.1, client=K8S.get_cord_k8s_api()
    )

app.add_exception_handler(RequestValidationError, handle_request_validation_error)

app.include_router(endpoints.user_management.users_router)
app.include_router(endpoints.user_management.organization_router)

if ENABLE_TRACING:
    logger.info("Tracing enabled, enabling OpenTelemetry tracing instrumentation.")
    FastAPITelemetry.instrument(app)
