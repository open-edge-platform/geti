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

func TestInvalidRoi(t *testing.T) {
	roi := "10, 15, 30"
	// Invalid number of coordinates
	_, errROI := RoiFromString(roi)
	expectedErrorMsg := "Invalid ROI parameter provided: 10, 15, 30. Expected format for the ROI is `<int, int, int, int>`, corresponding to `<left, top, width, height>` pixel coordinates."
	assert.EqualErrorf(t, errROI, expectedErrorMsg, "Expected error message not found!")

	// Floating point coordinate in ROI
	roi = "10.5, 15, 30, 40"
	_, errROI = RoiFromString(roi)
	expectedErrorMsg = "Invalid ROI coordinate provided. Expected format for the ROI is `<int, int, int, int>`, corresponding to `<left, top, width, height>` pixel coordinates. Parser raised error: `strconv.Atoi: parsing \"10.5\": invalid syntax`"
	assert.EqualErrorf(t, errROI, expectedErrorMsg, "Expected error message not found!")
}
