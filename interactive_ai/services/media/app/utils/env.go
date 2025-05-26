// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"os"
	"strconv"

	"geti.com/iai_core/logger"
)

func GetStringEnvOrDefault(envVarName string, defaultValue string) string {
	envVarValue := os.Getenv(envVarName)
	if envVarValue == "" {
		return defaultValue
	}
	return envVarValue
}

func GetIntEnvOrDefault(envVarName string, defaultValue int) int {
	envVarValue := os.Getenv(envVarName)
	if envVarValue == "" {
		return defaultValue
	}
	envVarValueConverted, err := strconv.Atoi(envVarValue)
	if err != nil {
		logger.Log().Warnf("couldn't parse %v , err: \"%v\" , falling back to default", envVarValue, err)
		return defaultValue
	}
	return envVarValueConverted
}

func GetBoolEnvOrDefault(envVarName string, defaultValue bool) bool {
	envVarValue := os.Getenv(envVarName)
	if envVarValue == "" {
		return defaultValue
	}
	envVarValueConverted, err := strconv.ParseBool(envVarValue)
	if err != nil {
		logger.Log().Warnf("couldn't parse %v , err: \"%v\" , falling back to default", envVarValue, err)
		return defaultValue
	}
	return envVarValueConverted
}
