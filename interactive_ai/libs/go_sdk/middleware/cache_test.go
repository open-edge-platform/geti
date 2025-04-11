// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
