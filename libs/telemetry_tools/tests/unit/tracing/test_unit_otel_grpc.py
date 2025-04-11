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
