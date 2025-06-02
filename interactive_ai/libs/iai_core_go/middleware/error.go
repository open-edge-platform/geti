// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package middleware

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"

	httperrors "geti.com/iai_core/errors"
	"geti.com/iai_core/logger"
)

func ErrorHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()

		ctx := c.Request.Context()
		if len(c.Errors) > 0 {
			{
				var httpErr *httperrors.HTTPError
				err := c.Errors[0].Err
				switch {
				case errors.As(err, &httpErr):
					logger.TracingLog(ctx).
						Errorf("Error %d (%s): %s.", httpErr.StatusCode, httpErr.ErrorCode, httpErr.Message)
					c.JSON(
						httpErr.StatusCode,
						gin.H{
							"message":     httpErr.Message,
							"error_code":  httpErr.ErrorCode,
							"http_status": httpErr.StatusCode,
						},
					)
				default:
					logger.TracingLog(ctx).Errorf("Internal server error: %s", err)
					c.JSON(
						http.StatusInternalServerError,
						gin.H{
							"message":     err.Error(),
							"error_code":  "internal_server_error",
							"http_status": http.StatusInternalServerError,
						},
					)
				}
			}
		}
	}
}
