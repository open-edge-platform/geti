// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"os"
	"strconv"
	"time"
)

// GetEnv tries to get an environment variable. If it is not found the fallback value is returned.
func GetEnv(key string, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

// GetEnvAsInt tries to get an environment variable and parse it as an int. If it is not found or cannot be parsed the fallback value is returned.
func GetEnvAsInt(key string, fallback string) (int, error) {
	value := GetEnv(key, fallback)
	intValue, err := strconv.Atoi(value)
	if err != nil {
		return 0, err
	}
	return intValue, nil
}

// GetEnvAsDuration tries to get an environment variable and parse it as a time.Duration. If it is not found or cannot be parsed the fallback value is returned.
func GetEnvAsDuration(key string, fallback string) (time.Duration, error) {
	value := GetEnv(key, fallback)
	period, err := time.ParseDuration(value)
	if err != nil {
		return 0, err
	}
	return period, nil
}
