// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestValidateID(t *testing.T) {
	validID := ID{"012345678910abcdefABCDEF"}
	invalidID := ID{"001"}

	assert.Nil(t, validID.IsValid())
	assert.NotNil(t, invalidID.IsValid())
}

func TestEmptyID(t *testing.T) {
	emptyID := ID{""}

	assert.True(t, emptyID.IsEmptyID())
	assert.NotNil(t, emptyID.IsValid())
}
