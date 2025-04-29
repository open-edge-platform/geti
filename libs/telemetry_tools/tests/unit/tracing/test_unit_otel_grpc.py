# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from opentelemetry.instrumentation.grpc import (  # type: ignore[attr-defined]
    GrpcInstrumentorClient,
    GrpcInstrumentorServer,
)

from geti_telemetry_tools import GrpcClientTelemetry, GrpcServerTelemetry


class TestUnitOtelGrpc:
    def test_instrument_uninstrument_client(self) -> None:
        """Test that gRPC client can be instrumented and un-instrumented."""
        assert not GrpcInstrumentorClient()._is_instrumented_by_opentelemetry

        GrpcClientTelemetry.instrument()
        assert GrpcInstrumentorClient()._is_instrumented_by_opentelemetry

        GrpcClientTelemetry.uninstrument()
        assert not GrpcInstrumentorClient()._is_instrumented_by_opentelemetry

    def test_instrument_uninstrument_server(self) -> None:
        """Test that gRPC server can be instrumented and un-instrumented."""
        assert not GrpcInstrumentorServer()._is_instrumented_by_opentelemetry

        GrpcServerTelemetry.instrument()
        assert GrpcInstrumentorServer()._is_instrumented_by_opentelemetry

        GrpcServerTelemetry.uninstrument()
        assert not GrpcInstrumentorServer()._is_instrumented_by_opentelemetry
