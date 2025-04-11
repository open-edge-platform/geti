// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/stretchr/testify/assert"
)

func TestGenerateRandomString(t *testing.T) {
	str := GenerateRandomString(10)
	assert.Equal(t, 10, len(str))

	str = GenerateRandomString(0)
	assert.Equal(t, 0, len(str))
}

func TestGetAuthenticationTime(t *testing.T) {
	claims := jwt.MapClaims{
		"auth_time": float64(1633072800),
	}

	authTime, err := GetAuthenticationTime(claims)
	assert.NoError(t, err)
	assert.Equal(t, time.Unix(1633072800, 0), authTime)

	claims["auth_time"] = json.Number("1633072800")
	authTime, err = GetAuthenticationTime(claims)
	assert.NoError(t, err)
	assert.Equal(t, time.Unix(1633072800, 0), authTime)

	claims["auth_time"] = "invalid"
	_, err = GetAuthenticationTime(claims)
	assert.Error(t, err)
}
