// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestValidateID(t *testing.T) {
	validID := ID{"012345678910abcdefABCDEF"}
	invalidID := ID{"001"}

	require.NoError(t, validID.IsValid())
	require.Error(t, invalidID.IsValid())
}

func TestEmptyID(t *testing.T) {
	emptyID := ID{""}

	assert.True(t, emptyID.IsEmpty())
	require.Error(t, emptyID.IsValid())
}
