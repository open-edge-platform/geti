# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

"""Helpers for the integration of OpenTelemetry with logging"""

from geti_telemetry_tools.tracing.common import tracer_provider


class LoggerTelemetry:
    """OpenTelemetry instrumentation for logging"""

    @staticmethod
    def instrument() -> None:
        """
        Instruments logging module.

        Instrumentor sets new log record factory which is able to extract trace ID, span ID and service name from
        tracing context and put it as a log record custom fields.
        """
        # NOTE: do not use the logger within this method. It modifies the logging adapters, so depending on the format
        # (configured outside of this function), it could raise errors due to missing formatting fields in the record.
        try:
            from opentelemetry.instrumentation.logging import LoggingInstrumentor  # type: ignore[attr-defined]
        except ImportError as err:
            raise Exception(
                "Cannot instrument logging because opentelemetry-instrumentation-logging "
                "is not installed. Add 'telemetry[logger]' to the required packages."
            ) from err

        LoggingInstrumentor().instrument(tracer_provider=tracer_provider)
