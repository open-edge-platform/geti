// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package middleware

import (
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/uptrace/opentelemetry-go-extra/otelzap"
	"go.uber.org/zap"
	"go.uber.org/zap/zaptest/observer"
)

func TestLoggerWithZapMiddleware(t *testing.T) {
	core, recorded := observer.New(zap.InfoLevel)
	mockLogger := otelzap.New(zap.New(core))

	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(ZapRequestLogger(mockLogger))

	r.GET("/test", func(c *gin.Context) {
		c.String(200, "Hello World")
	})

	req := httptest.NewRequest(http.MethodGet, "/test", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, 1, recorded.Len(), "Expected 1 log entry, got %d", recorded.Len())
	entry := recorded.All()[0]

	assert.Equal(t, zap.InfoLevel, entry.Level)
	assert.Equal(t, "http_request", entry.Message)

	fields := map[string]zap.Field{}
	for _, f := range entry.Context {
		fields[f.Key] = f
	}

	assert.Contains(t, fields, "status")
	assert.Equal(t, int64(200), fields["status"].Integer)

	assert.Contains(t, fields, "method")
	assert.Equal(t, "GET", fields["method"].String)

	assert.Contains(t, fields, "path")
	assert.Equal(t, "/test", fields["path"].String)

	assert.Contains(t, fields, "query")
	assert.Empty(t, fields["query"].String)

	assert.Contains(t, fields, "latency")
	latencyStr := fields["latency"].String
	numStr := strings.TrimSuffix(latencyStr, "ms")
	latencyVal, err := strconv.ParseFloat(numStr, 64)
	require.NoError(t, err, "should be able to parse latency value")
	assert.Greater(t, latencyVal, 0.0, "latency should be > 0 ms")

	assert.Contains(t, fields, "bytes_in")
	assert.Equal(t, int64(0), fields["bytes_in"].Integer)

	assert.Contains(t, fields, "bytes_out")
	assert.Equal(t, int64(len("Hello World")), fields["bytes_out"].Integer)

	assert.Contains(t, fields, "ip")
}
