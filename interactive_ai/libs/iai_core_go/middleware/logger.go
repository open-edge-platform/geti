// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package middleware

import (
	"fmt"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/uptrace/opentelemetry-go-extra/otelzap"
	"go.uber.org/zap"
)

func ZapRequestLogger(logger *otelzap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()

		path := c.Request.URL.EscapedPath()
		query := c.Request.URL.RawQuery
		method := c.Request.Method
		ip := c.ClientIP()

		c.Next()

		latency := time.Since(start)
		latencyFormatted := fmt.Sprintf("%.4fms", float64(latency.Nanoseconds())/float64(time.Millisecond))
		status := c.Writer.Status()
		sizeOut := c.Writer.Size()
		sizeIn := c.Request.ContentLength

		logger.Info("http_request",
			zap.Int("status", status),
			zap.String("latency", latencyFormatted),
			zap.String("ip", ip),
			zap.String("method", method),
			zap.String("path", path),
			zap.String("query", query),
			zap.Int64("bytes_in", sizeIn),
			zap.Int("bytes_out", sizeOut),
		)
	}
}
