// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"testing"

	configPb "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	extProcPb "github.com/envoyproxy/go-control-plane/envoy/service/ext_proc/v3"
	"github.com/stretchr/testify/assert"
)

func TestGetHeaderValue(t *testing.T) {
	headers := &extProcPb.HttpHeaders{
		Headers: &configPb.HeaderMap{
			Headers: []*configPb.HeaderValue{
				{
					Key:   "content-type",
					Value: "application/json",
				},
				{
					Key:      "authorization",
					RawValue: []byte("Bearer token"),
				},
			},
		},
	}

	value, found := GetHeaderValue(headers, "content-type")
	assert.True(t, found)
	assert.Equal(t, "application/json", value)

	value, found = GetHeaderValue(headers, "authorization")
	assert.True(t, found)
	assert.Equal(t, "Bearer token", value)

	value, found = GetHeaderValue(headers, "non-existent-header")
	assert.False(t, found)
	assert.Equal(t, "", value)
}

func TestGetHeaderValue_NilHeaders(t *testing.T) {
	value, found := GetHeaderValue(nil, "content-type")
	assert.False(t, found)
	assert.Equal(t, "", value)
}
