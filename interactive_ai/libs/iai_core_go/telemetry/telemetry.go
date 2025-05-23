// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

	"geti.com/iai_core/env"
	"geti.com/iai_core/logger"
)

// Middleware is the wrapper around otelgin.Middleware and returns a middleware for gin to trace incoming requests.
func Middleware() gin.HandlerFunc {
	serviceName := env.GetEnv("OTEL_SERVICE_NAME", "")
	return otelgin.Middleware(serviceName)
}

// SetupTracing initializes open-telemetry tracing.
// This function should be triggered at the start of the app.
// Returns shutdown function used for cleanup.
func SetupTracing(ctx context.Context) func() {
	var (
		err      error
		exporter sdktrace.SpanExporter
	)
	otlpTracesReceiver := env.GetEnv("OTLP_TRACES_RECEIVER", "")

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
		if err = tracerProvider.Shutdown(ctx); err != nil {
			logger.Log().Errorf("Cannot shutdown exporter: %v", err)
		}
	}
	return shutdown
}

// Tracer creates tracer with serviceName name.
func Tracer() trace.Tracer {
	serviceName := env.GetEnv("OTEL_SERVICE_NAME", "")
	return otel.Tracer(serviceName)
}

// RecordError marks span with error by adding error information to it.
func RecordError(span trace.Span, err error) {
	span.SetStatus(codes.Error, err.Error())
	span.RecordError(err)
}
