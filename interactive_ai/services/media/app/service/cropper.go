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

package service

import (
	"fmt"
	"image"
	"image/draw"
	"io"
	"math"

	"github.com/nfnt/resize"
)

type Cropper interface {
	CropImage(reader io.Reader, tWidth uint, tHeight uint) (image.Image, error)
}

type ResizeCropper struct {
}

func NewResizeCropper() *ResizeCropper {
	return new(ResizeCropper)
}

// CropImage This function will create the thumbnail image.
// It will first resize the initial image (media) to target the dimensions (tHeight, tWidth) by a scaling factor
// which causes the least amount of rescaling, then in it will crop out a tWidth x tHeight rectangle from the
// center of the resized media to make the thumbnail.
func (c ResizeCropper) CropImage(reader io.Reader, tWidth uint, tHeight uint) (image.Image, error) {
	media, _, err := image.Decode(reader)
	if err != nil {
		return nil, fmt.Errorf("cannot decode image: %s", err)
	}

	// Obtain the initial dimensions of the original media
	iHeight, iWidth := media.Bounds().Dy(), media.Bounds().Dx()

	// Determine which axis would need to be the least scaled
	sWidth := float64(tWidth) / float64(iWidth)
	sHeight := float64(tHeight) / float64(iHeight)
	sFactor := math.Max(sWidth, sHeight)

	// Resize the media's initial dimensions by sFactor, then obtain the new dimensions
	resizedMedia := resize.Resize(uint(float64(iWidth)*sFactor), uint(float64(iHeight)*sFactor), media, resize.Bicubic)
	nHeight, nWidth := resizedMedia.Bounds().Dy(), resizedMedia.Bounds().Dx()

	// Here we determine the min and max points of the crop rectangle. The rectangle which has its center at the center
	// of resizedMedia. The min and the max values must be clamped to be in the interval [0, new_size]
	xMin := (nWidth - int(tWidth)) / 2
	xMax := xMin + int(tWidth)
	xMin = int(math.Max(float64(xMin), 0))
	xMax = int(math.Min(float64(xMax), float64(nWidth)))
	yMin := (nHeight - int(tHeight)) / 2
	yMax := yMin + int(tHeight)
	yMin = int(math.Max(float64(yMin), 0))
	yMax = int(math.Min(float64(yMax), float64(nHeight)))
	minPoint := image.Point{X: xMin, Y: yMin}
	maxPoint := image.Point{X: xMax, Y: yMax}
	cropRect := image.Rectangle{
		Min: minPoint,
		Max: maxPoint,
	}

	// Generate a new blank RGBA image of size cropRect which will be the destination image for the crop
	croppedMedia := image.NewRGBA(cropRect)

	// Crop a shape of size cropRect from the resizedMedia (source) onto the croppedMedia (destination), starting at
	// top left rectangle point (minPoint) in the resizedMedia.
	draw.Draw(croppedMedia, cropRect, resizedMedia, minPoint, draw.Src)
	return croppedMedia, nil
}
