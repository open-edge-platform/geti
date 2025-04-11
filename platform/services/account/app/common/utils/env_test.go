// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGetStringEnvOrDefaultVarSet(t *testing.T) {
	fakeEnvVarName := "FAKE_ENV"
	fakeEnvVarValue := "fake-value"
	fakeDefault := "fake-default"
	err := os.Setenv(fakeEnvVarName, fakeEnvVarValue)
	if err != nil {
		t.Fatalf("%v", err)
	}
	envVarValue := GetStringEnvOrDefault(fakeEnvVarName, fakeDefault)
	err = os.Setenv(fakeEnvVarName, "")
	if err != nil {
		t.Fatalf("%v", err)
	}
	assert.Equal(t, fakeEnvVarValue, envVarValue)

}

func TestGetStringEnvOrDefaultRealVarUnset(t *testing.T) {
	fakeEnvVarName := "FAKE_ENV"
	fakeDefault := "fake-default"
	envVarValue := GetStringEnvOrDefault(fakeEnvVarName, fakeDefault)

	assert.Equal(t, fakeDefault, envVarValue)
}
