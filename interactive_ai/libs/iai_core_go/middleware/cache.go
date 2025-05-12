// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package middleware

import (
	"github.com/gin-gonic/gin"
)

func CacheControl() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()

		statusCode := c.Writer.Status()
		if statusCode == 204 || statusCode >= 400 {
			c.Writer.Header().Set("Cache-Control", "no-cache")
		}
	}
}
