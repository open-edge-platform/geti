// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestLoadAuthProxyConfiguration(t *testing.T) {
	os.Setenv("ISS_INTERNAL", "internal_issuer")
	os.Setenv("AUD_INTERNAL", "internal_audience")
	os.Setenv("ISS_EXTERNAL", "external_issuer")
	os.Setenv("AUD_EXTERNAL", "external_audience")
	os.Setenv("REQUIRED_ROLES", "role1,role2")

	config, err := LoadAuthProxyConfiguration()
	assert.NoError(t, err)
	assert.NotNil(t, config)
	assert.Equal(t, "internal_issuer", config.IssInternal)
	assert.Equal(t, "internal_audience", config.AudInternal)
	assert.Equal(t, "external_issuer", config.IssExternal)
	assert.Equal(t, "external_audience", config.AudExternal)
	assert.Equal(t, []string{"role1", "role2"}, config.RequiredRoles)
}

func TestGetJwtTtlGeti(t *testing.T) {
	os.Setenv("JWT_TTL_GETI", "30m")
	duration, err := GetJwtTtlGeti()
	assert.NoError(t, err)
	assert.Equal(t, 30*time.Minute, duration)
}

func TestGetCacheTtl(t *testing.T) {
	os.Setenv("CACHE_TTL_SECONDS", "120")
	ttl, err := GetCacheTtl()
	assert.NoError(t, err)
	assert.Equal(t, 120, ttl)
}

func TestGetCacheSizeMB(t *testing.T) {
	os.Setenv("CACHE_SIZE_MB", "20")
	size, err := GetCacheSizeMB()
	assert.NoError(t, err)
	assert.Equal(t, 20, size)
}

func TestGetUnauthorizedURLs(t *testing.T) {
	os.Setenv("UNAUTHORIZED_URLS", "/api/v1/test1,/api/v1/test2")
	urls := GetUnauthorizedURLs()
	assert.Equal(t, []string{"/api/v1/test1", "/api/v1/test2"}, urls)
}
