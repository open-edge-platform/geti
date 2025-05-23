// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package testhelpers

import (
	"fmt"
	"image"
	"image/color"
	"image/draw"

	sdkentities "geti.com/iai_core/entities"
)

// GetUniformTestImage returns a uniform grayscale image of dimensions `Dx` * `Dy` (width * heigth)
// The pixel values will be set to `grayscaleColor`.
func GetUniformTestImage(dx int, dy int, grayscaleColor uint8) image.Image {
	img := image.NewRGBA(image.Rect(0, 0, dx, dy))
	draw.Draw(img, img.Bounds(), image.NewUniform(color.Gray{Y: grayscaleColor}), image.Point{}, draw.Src)
	return img
}

// NewDummyID returns a dummy ID for test purposes.
func NewDummyID(value int) sdkentities.ID {
	const idLength int = 24
	return sdkentities.ID{ID: fmt.Sprintf("%0*d", idLength, value)}
}
