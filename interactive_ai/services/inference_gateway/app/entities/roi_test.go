// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"testing"

	"github.com/stretchr/testify/require"
)

func TestInvalidRoi(t *testing.T) {
	roi := "10, 15, 30"
	// Invalid number of coordinates
	_, errROI := RoiFromString(roi)
	expectedErrorMsg := "Invalid ROI parameter provided: 10, 15, 30. Expected format for the ROI is `<int, int, int, int>`, corresponding to `<left, top, width, height>` pixel coordinates."
	require.EqualErrorf(t, errROI, expectedErrorMsg, "Expected error message not found!")

	// Floating point coordinate in ROI
	roi = "10.5, 15, 30, 40"
	_, errROI = RoiFromString(roi)
	expectedErrorMsg = "Invalid ROI coordinate provided. Expected format for the ROI is `<int, int, int, int>`, corresponding to `<left, top, width, height>` pixel coordinates. Parser raised error: `strconv.Atoi: parsing \"10.5\": invalid syntax`"
	require.EqualErrorf(t, errROI, expectedErrorMsg, "Expected error message not found!")
}
