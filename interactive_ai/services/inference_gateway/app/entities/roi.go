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
	"fmt"
	"strconv"
	"strings"

	httperrors "geti.com/go_sdk/errors"
)

type Roi struct {
	X      int
	Y      int
	Width  int
	Height int
}

// IsNull Checks if ROI has empty values
func (roi *Roi) IsNull() bool {
	return roi.X == 0 && roi.Y == 0 && roi.Width == 0 && roi.Height == 0
}

func RoiFromString(roi string) (Roi, error) {
	if roi == "" {
		return Roi{0, 0, 0, 0}, nil
	}
	roiStrings := strings.SplitN(roi, ",", -1)
	expectedFormatErrorMsg := "Expected format for the ROI is `<int, int, int, int>`, corresponding to `<left, top, width, height>` pixel coordinates."

	if len(roiStrings) != 4 {
		e := httperrors.NewBadRequestError(
			fmt.Sprintf(
				"Invalid ROI parameter provided: %s. %s",
				roi,
				expectedFormatErrorMsg,
			),
		)
		return Roi{}, e
	}
	x, errLeft := strconv.Atoi(strings.TrimSpace(roiStrings[0]))
	y, errTop := strconv.Atoi(strings.TrimSpace(roiStrings[1]))
	width, errWidth := strconv.Atoi(strings.TrimSpace(roiStrings[2]))
	height, errHeight := strconv.Atoi(strings.TrimSpace(roiStrings[3]))
	conversionErrors := [4]error{errTop, errLeft, errHeight, errWidth}
	for _, value := range conversionErrors {
		if value != nil {
			e := httperrors.NewBadRequestError(
				fmt.Sprintf(
					"Invalid ROI coordinate provided. %s Parser raised error: `%s`",
					expectedFormatErrorMsg,
					value,
				),
			)
			return Roi{}, e
		}
	}
	return Roi{X: x, Y: y, Width: width, Height: height}, nil
}
