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
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	httperrors "geti.com/go_sdk/errors"
)

func TestErrorHandler(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name     string
		path     string
		giveErr  error
		wantJSON string
		wantCode int
	}{
		{
			name:    "HTTPError",
			path:    "/test-http-error",
			giveErr: httperrors.NewBadRequestError("test"),
			wantJSON: `{
					    "error_code": "bad_request",
						"http_status": 400,
						"message": "test"
                      }`,
			wantCode: http.StatusBadRequest,
		},
		{
			name:    "NonHTTPError",
			path:    "/test-no-http-error",
			giveErr: errors.New("test"),
			wantJSON: `{
						"error_code": "internal_server_error",
						"http_status": 500,
						"message": "test"
				      }`,
			wantCode: http.StatusInternalServerError,
		},
	}

	router := gin.New()
	router.Use(ErrorHandler())

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			router.GET(tt.path, func(c *gin.Context) {
				_ = c.Error(tt.giveErr)
			})
			req, _ := http.NewRequest("GET", tt.path, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)
			assert.Equal(t, tt.wantCode, resp.Code)
			assert.JSONEq(t, tt.wantJSON, resp.Body.String(), "The JSON bodies should match")
		})
	}
}
