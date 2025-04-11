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

	"github.com/gin-gonic/gin"

	"geti.com/go_sdk/errors"
	"geti.com/go_sdk/logger"
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
