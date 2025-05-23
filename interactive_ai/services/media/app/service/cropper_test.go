// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package service

import (
	"bytes"
	"image"
	"image/png"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
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

	require.NoError(t, err)

	// the resulting image should be a 50x50 thumbnail
	assert.Equal(t, 50, thumbnail.Bounds().Dx())
	assert.Equal(t, 50, thumbnail.Bounds().Dy())
}

func TestResizeAndCropImage_NotMedia(t *testing.T) {
	resizeCropper := ResizeCropper{}
	// pass the function our media, and request a 50x50 thumbnail
	thumbnail, err := resizeCropper.CropImage(strings.NewReader("not_media"), 50, 50)

	require.Error(t, err)
	assert.Nil(t, thumbnail)
}
