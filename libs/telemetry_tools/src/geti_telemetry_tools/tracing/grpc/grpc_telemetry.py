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

"""Utilities to instrument gRPC clients and servers with OpenTelemetry"""

import logging

logger = logging.getLogger(__name__)


class GrpcClientTelemetry:
    """OpenTelemetry instrumentation for gRPC clients"""

    @staticmethod
    def instrument() -> None:
        """Instrument gRPC clients."""
        try:
            from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient  # type: ignore[attr-defined]
        except ImportError:
            logger.exception(
                "Cannot instrument gRPC because opentelemetry-instrumentation-grpc "
                "is not installed. Add 'telemetry[grpc]' to the required packages."
            )
            raise

        grpc_client_instrumentor = GrpcInstrumentorClient()
        if not grpc_client_instrumentor.is_instrumented_by_opentelemetry:
            grpc_client_instrumentor.instrument()

    @staticmethod
    def uninstrument() -> None:
        """Uninstrument gRPC clients."""
        try:
            from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient  # type: ignore[attr-defined]
        except ImportError:
            logger.error(
                "Cannot instrument gRPC because opentelemetry-instrumentation-grpc "
                "is not installed. Add 'telemetry[grpc]' to the required packages."
            )
            raise

        grpc_client_instrumentor = GrpcInstrumentorClient()
        if grpc_client_instrumentor.is_instrumented_by_opentelemetry:
            grpc_client_instrumentor.uninstrument()


class GrpcServerTelemetry:
    """OpenTelemetry instrumentation for gRPC servers"""

    @staticmethod
    def instrument() -> None:
        """Instrument gRPC servers."""
        try:
            from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer  # type: ignore[attr-defined]
        except ImportError:
            logger.exception(
                "Cannot instrument gRPC because opentelemetry-instrumentation-grpc "
                "is not installed. Add 'telemetry[grpc]' to the required packages."
            )
            raise

        grpc_server_instrumentor = GrpcInstrumentorServer()
        if not grpc_server_instrumentor.is_instrumented_by_opentelemetry:
            grpc_server_instrumentor.instrument()

    @staticmethod
    def uninstrument() -> None:
        """Uninstrument gRPC servers."""
        try:
            from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer  # type: ignore[attr-defined]
        except ImportError:
            logger.exception(
                "Cannot instrument gRPC because opentelemetry-instrumentation-grpc "
                "is not installed. Add 'telemetry[grpc]' to the required packages."
            )
            raise

        grpc_server_instrumentor = GrpcInstrumentorServer()
        if grpc_server_instrumentor.is_instrumented_by_opentelemetry:
            grpc_server_instrumentor.uninstrument()
