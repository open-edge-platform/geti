// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package cache

import (
	"encoding/json"
	asc "geti.com/account_service_grpc"
	"github.com/coocood/freecache"
)

type Cache struct {
	cache *freecache.Cache
	ttl   int
}

type UserDataCache struct {
	*asc.User
	GetiJWT string `json:"getiJWT"`
}

type AccessTokenCache struct {
	*asc.AccessTokenData
	GetiJWT  string `json:"getiJWT"`
	ErrorMsg string `json:"errorMsg"`
}

// NewCache creates a new cache with the defined in seconds expiration (TTL)
func NewCache(cacheTTL int, cacheSizeMB int) *Cache {
	return &Cache{
		cache: freecache.NewCache(cacheSizeMB * 1024 * 1024),
		ttl:   cacheTTL,
	}
}

// SetUserDataCache stores the user data in the cache with the defined ttl, JWT subject is used as the key
func (c *Cache) SetUserDataCache(jwtSubject string, data UserDataCache) error {
	value, err := json.Marshal(data)
	if err != nil {
		return err
	}
	return c.cache.Set([]byte(jwtSubject), value, c.ttl)
}

// GetUserDataCache retrieves the user data from the cache using the JWT subject as the key
func (c *Cache) GetUserDataCache(jwtSubject string) (*UserDataCache, error) {
	value, err := c.cache.Get([]byte(jwtSubject))
	if err != nil {
		return nil, err
	}
	var data UserDataCache
	err = json.Unmarshal(value, &data)
	if err != nil {
		return nil, err
	}
	return &data, nil
}

// SetAccessTokenCache stores the access token data in the cache with the defined ttl, token hash is used as the key
func (c *Cache) SetAccessTokenCache(tokenHash string, data AccessTokenCache) error {
	value, err := json.Marshal(data)
	if err != nil {
		return err
	}
	return c.cache.Set([]byte(tokenHash), value, c.ttl)
}

// GetAccessTokenCache retrieves the access token data from the cache using the token hash as the key
func (c *Cache) GetAccessTokenCache(tokenHash string) (*AccessTokenCache, error) {
	value, err := c.cache.Get([]byte(tokenHash))
	if err != nil {
		return nil, err
	}
	var data AccessTokenCache
	err = json.Unmarshal(value, &data)
	if err != nil {
		return nil, err
	}
	return &data, nil
}

func (c *Cache) DeleteCacheEntry(key string) bool {
	return c.cache.Del([]byte(key))
}
