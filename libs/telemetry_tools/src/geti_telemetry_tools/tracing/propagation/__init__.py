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
