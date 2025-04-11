// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
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
