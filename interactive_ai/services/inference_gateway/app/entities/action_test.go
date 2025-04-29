// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestIsActionSupported(t *testing.T) {
	validAction := "predict"
	invalidAction := "invalid_action"

	assert.True(t, IsActionSupported(validAction))
	assert.False(t, IsActionSupported(invalidAction))
}

func TestSupportedActionsInSync(t *testing.T) {
	var actions []ActionType
	for action := range supportedActions {
		actions = append(actions, action)
	}

	assert.ElementsMatch(t, actions, SupportedActions)
}
