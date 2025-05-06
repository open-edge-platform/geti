// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package frames

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"

	"geti.com/iai_core/entities"
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
