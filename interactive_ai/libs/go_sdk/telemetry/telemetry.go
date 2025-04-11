// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package telemetry

import (
	"context"

	"github.com/gin-gonic/gin"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/trace"

	"geti.com/go_sdk/env"
	"geti.com/go_sdk/logger"
)

var (
	serviceName        = env.GetEnv("OTEL_SERVICE_NAME", "")
	otlpTracesReceiver = env.GetEnv("OTLP_TRACES_RECEIVER", "")
)

// Middleware is the wrapper around otelgin.Middleware and returns a middleware for gin to trace incoming requests.
func Middleware() gin.HandlerFunc {
	return otelgin.Middleware(serviceName)
}

// SetupTracing initializes open-telemetry tracing.
// This function should be triggered at the start of the app.
// Returns shutdown function used for cleanup.
func SetupTracing(ctx context.Context) func() {
	var exporter sdktrace.SpanExporter
	var err error

	if otlpTracesReceiver != "" {
		exporter, err = otlptrace.New(
			ctx,
			otlptracegrpc.NewClient(
				otlptracegrpc.WithInsecure(),
				otlptracegrpc.WithEndpoint(otlpTracesReceiver),
			),
		)
		logger.Log().Infof("Sending trace data to %s", otlpTracesReceiver)
	} else {
		logger.Log().Info("No trace receiver endpoint configured")
	}

	if err != nil {
		logger.Log().Fatalf("Could not set exporter: %s", err)
	}
	resources, err := resource.New(ctx, resource.WithFromEnv())

	if err != nil {
		logger.Log().Fatalf("Could not set resources: %s", err)
	}

	tracerProvider := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resources),
	)
	propagator := propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{})

	otel.SetTracerProvider(tracerProvider)
	otel.SetTextMapPropagator(propagator)

	shutdown := func() {
		if err := tracerProvider.Shutdown(ctx); err != nil {
			logger.Log().Errorf("Cannot shutdown exporter: %v", err)
		}
	}
	return shutdown
}

// Tracer creates tracer with serviceName name.
func Tracer() trace.Tracer {
	return otel.Tracer(serviceName)
}

// RecordError marks span with error by adding error information to it.
func RecordError(span trace.Span, err error) {
	span.SetStatus(codes.Error, err.Error())
	span.RecordError(err)
}
