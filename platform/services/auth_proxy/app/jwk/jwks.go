// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package jwk

import (
	"encoding/json"
	"time"

	"auth_proxy/app/utils"
)

var JWKS_UPDATE_TIME, _ = utils.GetEnvAsDuration("JWKS_UPDATE_TIME", "1s")
var JWK_ENTRY_EXPIRATION, _ = utils.GetEnvAsDuration("JWK_ENTRY_EXPIRATION", "15m")

var cachedJWKsResponse = ""

// JWKsCacheEntry represents a cache entry for a JWK with an expiration time
type JWKsCacheEntry struct {
	JWK       JWK       `json:"jwk"`
	ExpiresAt time.Time `json:"expires_at"`
}

// jwkCache stores a mapping from kid to JWKsCacheEntry
var jwkCache = make(map[string]JWKsCacheEntry)

func GetJWKs() string {
	return cachedJWKsResponse
}

func ScheduleJWKSUpdate() {
	scheduleJWKSUpdate(JWKS_UPDATE_TIME, &FileReaderKeysProvider{})
}

func scheduleJWKSUpdate(d time.Duration, provider KeyProvider) {
	logger.Debugf("Scheduling JWKS update every %v", d)
	update(provider)

	ticker := time.NewTicker(d)
	defer ticker.Stop()

	for range ticker.C {
		update(provider)
	}
}

func update(provider KeyProvider) {
	logger.Debug("Updating JWKS")

	publicKey, err := provider.PublicKey()
	if err != nil {
		logger.Errorf("Failed to get public key: %v", err)
		return
	}

	jwk, err := FromPEM(publicKey)
	if err != nil {
		logger.Errorf("Failed to create JWK from Public key PEM: %v", err)
		return
	}

	AddJWK(jwk)
}

func AddJWK(jwk JWK) {
	cacheEntry := JWKsCacheEntry{
		JWK:       jwk,
		ExpiresAt: time.Now().Add(JWK_ENTRY_EXPIRATION),
	}
	jwkCache[jwk.Kid] = cacheEntry

	updateCachedResponse()

	logger.Debugf("Added JWK with kid %s to cache", jwk.Kid)
}

func updateCachedResponse() {
	removeOutdated()

	var jwks []JWK
	for _, entry := range jwkCache {
		jwks = append(jwks, entry.JWK)
	}
	jwksResp := map[string]interface{}{
		"keys": jwks,
	}
	jwksJSON, err := json.MarshalIndent(jwksResp, "", "  ")
	if err != nil {
		logger.Errorf("Failed to marshal JWKs to JSON: %v", err)
		cachedJWKsResponse = ""
		return
	}
	cachedJWKsResponse = string(jwksJSON)
}

func removeOutdated() {
	logger.Debug("Removing outdated JWKs from cache")
	now := time.Now()
	for kid, entry := range jwkCache {
		if entry.ExpiresAt.Before(now) {
			logger.Debugf("Removing JWK with kid %s from cache", kid)
			delete(jwkCache, kid)
		}
	}
}
