// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package testhelpers

import (
	"fmt"
	"image"
	"image/color"
	"image/draw"

	sdkentities "geti.com/go_sdk/entities"
)

// GetUniformTestImage returns a uniform grayscale image of dimensions `Dx` * `Dy` (width * heigth)
// The pixel values will be set to `grayscaleColor`
func GetUniformTestImage(Dx int, Dy int, grayscaleColor uint8) image.Image {
	img := image.NewRGBA(image.Rect(0, 0, Dx, Dy))
	draw.Draw(img, img.Bounds(), image.NewUniform(color.Gray{Y: grayscaleColor}), image.Point{}, draw.Src)
	return img
}

// NewDummyID returns a dummy ID for test purposes
func NewDummyID(value int) sdkentities.ID {
	const idLength int = 24
	return sdkentities.ID{ID: fmt.Sprintf("%0*d", idLength, value)}
}
