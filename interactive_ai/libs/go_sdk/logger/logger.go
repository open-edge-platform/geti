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

package logger

import (
	"context"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/uptrace/opentelemetry-go-extra/otelzap"
	"go.opentelemetry.io/otel/trace"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"geti.com/go_sdk/env"
)

var (
	logger          = otelzap.New(zap.NewNop())
	sugarLogger     = logger.Sugar()
	otelServiceName = env.GetEnv("OTEL_SERVICE_NAME", "")
	once            sync.Once
)

// Initialize initializes the logger with custom encoders if it's not initialized
func Initialize() {
	once.Do(func() {
		config := zap.NewProductionEncoderConfig()
		config.EncodeTime = timeEncoder
		config.EncodeLevel = levelEncoder
		config.EncodeCaller = callerEncoder

		consoleCore := zapcore.NewCore(
			zapcore.NewConsoleEncoder(config),
			zapcore.AddSync(os.Stdout),
			zapcore.InfoLevel)

		logger = otelzap.New(
			zap.New(
				consoleCore,
				zap.AddCaller(),
				zap.AddStacktrace(zapcore.ErrorLevel)))
		sugarLogger = logger.Sugar()
	})
}

// Log returns sugar version of the logger.
func Log() *otelzap.SugaredLogger {
	return sugarLogger
}

// TracingLog returns sugared logger with tracing information.
func TracingLog(ctx context.Context) *otelzap.SugaredLogger {
	// TODO: consider updating this code when otelzap will support tracing context propagation
	// https://github.com/uptrace/opentelemetry-go-extra/pull/126
	if span := trace.SpanFromContext(ctx); span != nil && span.IsRecording() {
		spanContext := span.SpanContext()
		return sugarLogger.With(
			"trace_id", spanContext.TraceID().String(),
			"span_id", spanContext.SpanID().String(),
			"resource.service.name", otelServiceName,
		)
	}
	return sugarLogger
}

func timeEncoder(t time.Time, enc zapcore.PrimitiveArrayEncoder) {
	enc.AppendString(t.Format("2006-01-02 15:04:05.999"))
}

func levelEncoder(level zapcore.Level, enc zapcore.PrimitiveArrayEncoder) {
	enc.AppendString(fmt.Sprintf("[%-8s]", level.CapitalString()))
}

func callerEncoder(caller zapcore.EntryCaller, enc zapcore.PrimitiveArrayEncoder) {
	enc.AppendString("[" + caller.TrimmedPath() + "]:")
}
