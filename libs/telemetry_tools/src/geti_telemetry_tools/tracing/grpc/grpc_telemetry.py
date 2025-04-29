# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
