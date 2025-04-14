# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Helpers for telemetry context propagation."""

import logging
import os

from opentelemetry.baggage.propagation import W3CBaggagePropagator  # type: ignore[attr-defined]
from opentelemetry.instrumentation.propagators import Setter
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.textmap import CarrierT
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

__all__ = ["HttpEncodedHeaderSetter", "HttpHeaderSetter", "propagator"]

logger = logging.getLogger(__name__)

OTEL_PROPAGATORS_ENV = "OTEL_PROPAGATORS"
env_propagators = os.environ.get(OTEL_PROPAGATORS_ENV, "tracecontext,baggage")
logger.info("Configured OpenTelemetry propagation format: %s", env_propagators)

try:
    from opentelemetry import propagate  # type: ignore[attr-defined]
except Exception:
    logger.error(
        "Some OpenTelemetry propagation modules are missing on not properly installed. "
        "Make sure to install the 'telemetry' package with the right extra deps. "
        "Defaulting to W3C TraceContext + Baggage format for now."
    )
    propagate.set_global_textmap(CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()]))

propagator = propagate.get_global_textmap()


class HttpHeaderSetter(Setter):
    """Setter for telemetry context injection in string-like HTTP headers"""

    def set(self, carrier: CarrierT, key: str, value: str) -> None:
        """
        Set a key-value pair of strings in an HTTP header.

        :param carrier: HTTP header (as dictionary)
        :param key: Key to set
        :param value: Value to set
        """
        carrier.append((key, value))


class HttpEncodedHeaderSetter(Setter):
    """Setter for telemetry context injection in UTF-8 encoded HTTP headers"""

    def set(self, carrier: CarrierT, key: str, value: str) -> None:
        """
        Set a key-value pair in an HTTP header with UTF-8 encoding.

        :param carrier: HTTP header (as dictionary of UTF-8 encoded key-value pairs)
        :param key: Key to set
        :param value: Value to set
        """
        carrier.append((key.encode(), value.encode()))
