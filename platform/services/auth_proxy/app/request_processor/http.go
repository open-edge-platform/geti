// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	extProcPb "github.com/envoyproxy/go-control-plane/envoy/service/ext_proc/v3"
	"strings"
)

const HeaderNameMethod = ":method"
const HeaderNamePath = ":path"
const HeaderNameScheme = ":scheme"
const HeaderNameAuthority = ":authority"
const HeaderNameStatus = ":status"
const HeaderNameLocation = "location"
const HeaderNameAuthorization = "authorization"
const HeaderNameXAuthRequestAccessToken = "x-auth-request-access-token"
const HeaderContentType = "content-type"
const HeaderApiKey = "x-api-key"

func GetHeaderValue(headers *extProcPb.HttpHeaders, key string) (string, bool) {
	if headers == nil {
		logger.Debugf("Headers are nil")
		return "", false
	}
	for _, h := range headers.Headers.Headers {
		if strings.ToLower(h.Key) == key {
			if h.Value != "" {
				logger.Debugf("Found header: %s, value: %s", h.Key, h.Value)
				return h.Value, true
			} else if len(h.RawValue) > 0 {
				rawValueStr := string(h.RawValue)
				logger.Debugf("Found header: %s, raw value: %s", h.Key, rawValueStr)
				return rawValueStr, true
			}
		}
	}
	logger.Debugf("Header %s not found", key)
	return "", false
}
