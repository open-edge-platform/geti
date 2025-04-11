// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
