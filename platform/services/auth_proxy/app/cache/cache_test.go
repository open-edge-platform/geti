// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package cache

import (
	"testing"

	asc "geti.com/account_service_grpc"
	"github.com/stretchr/testify/assert"
)

func TestCache_SetUserDataCache(t *testing.T) {
	cache := NewCache(60, 1) // 1MB cache with 60 seconds TTL
	userData := UserDataCache{
		User:    &asc.User{UserId: "123", FirstName: "TestUser"},
		GetiJWT: "test-jwt",
	}

	err := cache.SetUserDataCache("test-subject", userData)
	assert.NoError(t, err)

	cachedData, err := cache.GetUserDataCache("test-subject")
	assert.NoError(t, err)
	assert.Equal(t, userData, *cachedData)
}

func TestCache_GetUserDataCache_NotFound(t *testing.T) {
	cache := NewCache(60, 1) // 1MB cache with 60 seconds TTL

	cachedData, err := cache.GetUserDataCache("non-existent-subject")
	assert.Error(t, err)
	assert.Nil(t, cachedData)
}

func TestCache_SetAccessTokenCache(t *testing.T) {
	cache := NewCache(60, 1) // 1MB cache with 60 seconds TTL
	accessTokenData := AccessTokenCache{
		AccessTokenData: &asc.AccessTokenData{Id: "test-token"},
		GetiJWT:         "test-jwt",
		ErrorMsg:        "test-error",
	}

	err := cache.SetAccessTokenCache("test-token-hash", accessTokenData)
	assert.NoError(t, err)

	cachedData, err := cache.GetAccessTokenCache("test-token-hash")
	assert.NoError(t, err)
	assert.Equal(t, accessTokenData, *cachedData)
}

func TestCache_GetAccessTokenCache_NotFound(t *testing.T) {
	cache := NewCache(60, 1) // 1MB cache with 60 seconds TTL

	cachedData, err := cache.GetAccessTokenCache("non-existent-token-hash")
	assert.Error(t, err)
	assert.Nil(t, cachedData)
}

func TestCache_DeleteCacheEntry(t *testing.T) {
	cache := NewCache(60, 1) // 1MB cache with 60 seconds TTL
	userData := UserDataCache{
		User:    &asc.User{UserId: "123", FirstName: "Test User"},
		GetiJWT: "test-jwt",
	}

	err := cache.SetUserDataCache("test-subject", userData)
	assert.NoError(t, err)

	deleted := cache.DeleteCacheEntry("test-subject")
	assert.True(t, deleted)

	cachedData, err := cache.GetUserDataCache("test-subject")
	assert.Error(t, err)
	assert.Nil(t, cachedData)
}
