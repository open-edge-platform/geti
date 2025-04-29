// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package jwk

import (
	"encoding/json"
	"testing"
	"time"
)

func TestJWKEntryExpiration(t *testing.T) {
	tests := []struct {
		name          string
		jwk           JWK
		expiration    time.Duration
		expectedCount int
	}{
		{
			name: "JWK entry not expired",
			jwk: JWK{
				Kid: "test-kid-1",
				Use: "sig",
				Kty: "RSA",
				N:   "test-n",
				E:   "AQAB",
			},
			expiration:    15 * time.Minute,
			expectedCount: 1,
		},
		{
			name: "JWK entry expired",
			jwk: JWK{
				Kid: "test-kid-2",
				Use: "sig",
				Kty: "RSA",
				N:   "test-n",
				E:   "AQAB",
			},
			expiration:    -1 * time.Minute,
			expectedCount: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			jwkCache = make(map[string]JWKsCacheEntry) // Reset cache

			originalExpiration := JWK_ENTRY_EXPIRATION
			JWK_ENTRY_EXPIRATION = tt.expiration
			defer func() { JWK_ENTRY_EXPIRATION = originalExpiration }()

			AddJWK(tt.jwk)

			var jwksResp struct {
				Keys []JWK `json:"keys"`
			}
			err := json.Unmarshal([]byte(GetJWKs()), &jwksResp)
			if err != nil {
				t.Fatalf("Failed to unmarshal cached JWKs response: %v", err)
			}

			if len(jwksResp.Keys) != tt.expectedCount {
				t.Errorf("Expected cache count: %d, got: %d", tt.expectedCount, len(jwksResp.Keys))
			}
		})
	}
}
