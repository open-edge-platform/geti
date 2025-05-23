// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package middleware

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	httperrors "geti.com/iai_core/errors"
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
			req, _ := http.NewRequest(http.MethodGet, tt.path, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)
			assert.Equal(t, tt.wantCode, resp.Code)
			assert.JSONEq(t, tt.wantJSON, resp.Body.String(), "The JSON bodies should match")
		})
	}
}
