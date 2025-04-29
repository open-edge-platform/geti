// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestCacheControl(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name      string
		path      string
		giveCode  int
		wantCache string
	}{
		{
			name:      "NoCache",
			path:      "/test-error",
			giveCode:  404,
			wantCache: "no-cache",
		},
		{
			name:      "DefaultCache",
			path:      "/test-ok",
			giveCode:  200,
			wantCache: "",
		},
	}

	router := gin.New()
	router.Use(CacheControl())

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			router.GET(tt.path, func(c *gin.Context) {
				c.Status(tt.giveCode)
			})
			req, _ := http.NewRequest("GET", tt.path, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)
			assert.Equal(t, tt.wantCache, resp.Header().Get("Cache-Control"))
		})
	}
}
