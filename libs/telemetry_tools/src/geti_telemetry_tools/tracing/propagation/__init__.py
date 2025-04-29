# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Telemetry context propagation. Multiple propagation formats are supported.

W3C Trace Context: https://www.w3.org/TR/trace-context/
Open Zipkin B3: https://github.com/openzipkin/b3-propagation
Jaeger: https://www.jaegertracing.io/docs/1.21/client-libraries/#propagation-format

By default, OpenTelemetry uses the Trace Context format (traceparent + baggage).
To change format, set the OTEL_PROPAGATORS environment variable as documented here:
https://opentelemetry-python.readthedocs.io/en/latest/api/propagate.html
"""

from .context_propagator import HttpEncodedHeaderSetter, HttpHeaderSetter, propagator

__all__ = ["HttpEncodedHeaderSetter", "HttpHeaderSetter", "propagator"]
