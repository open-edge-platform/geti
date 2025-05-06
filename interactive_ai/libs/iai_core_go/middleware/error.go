// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package middleware

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"geti.com/iai_core/errors"
	"geti.com/iai_core/logger"
)

func ErrorHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()

		ctx := c.Request.Context()
		if len(c.Errors) > 0 {
			switch err := c.Errors[0].Err.(type) {
			case *errors.HTTPError:
				logger.TracingLog(ctx).Errorf("Error %d (%s): %s.", err.StatusCode, err.ErrorCode, err.Message)
				c.JSON(err.StatusCode, gin.H{
					"message":     err.Message,
					"error_code":  err.ErrorCode,
					"http_status": err.StatusCode,
				})
			default:
				logger.TracingLog(ctx).Errorf("Internal server error: %s", err)
				c.JSON(http.StatusInternalServerError, gin.H{
					"message":     err.Error(),
					"error_code":  "internal_server_error",
					"http_status": http.StatusInternalServerError,
				})
			}
		}
	}
}
