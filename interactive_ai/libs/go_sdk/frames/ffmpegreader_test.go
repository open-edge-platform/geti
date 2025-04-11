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

package frames

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"

	"geti.com/go_sdk/entities"
)

const VideoPath = "../test_data/test_mp4.mp4"

func TestReadFrameToBuffer(t *testing.T) {
	frameReader := new(FramerReaderImpl)
	_, err := frameReader.ReadFrameToBuffer(VideoPath, 0)
	assert.NoError(t, err)
}

func TestReadFrameToBufferFps(t *testing.T) {
	video := entities.NewVideo(context.Background(), VideoPath)
	frameReader := new(FramerReaderImpl)
	_, err := frameReader.ReadFrameToBufferFps(video.FilePath, 0, video.FPS)
	assert.NoError(t, err)
}
