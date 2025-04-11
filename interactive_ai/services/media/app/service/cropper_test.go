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
	"bytes"
	"image"
	"image/png"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestResizeAndCropImage(t *testing.T) {
	// create a new image, 100x100 pixels in size
	media := image.NewRGBA(image.Rect(0, 0, 100, 100))
	buf := new(bytes.Buffer)
	if err := png.Encode(buf, media); err != nil {
		t.Fatalf("Cannot encode media: %s", err)
	}

	resizeCropper := ResizeCropper{}
	// pass the function our media, and request a 50x50 thumbnail
	thumbnail, err := resizeCropper.CropImage(buf, 50, 50)

	assert.NoError(t, err)

	// the resulting image should be a 50x50 thumbnail
	assert.Equal(t, 50, thumbnail.Bounds().Dx())
	assert.Equal(t, 50, thumbnail.Bounds().Dy())
}

func TestResizeAndCropImage_NotMedia(t *testing.T) {
	resizeCropper := ResizeCropper{}
	// pass the function our media, and request a 50x50 thumbnail
	thumbnail, err := resizeCropper.CropImage(strings.NewReader("not_media"), 50, 50)

	assert.Error(t, err)
	assert.Nil(t, thumbnail)
}
