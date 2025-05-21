// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package frames

import (
	"context"
	"io"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"geti.com/iai_core/entities"
)

const (
	VPath            = "../test_data/test_mp4.mp4"
	start, end, skip = 20, 90, 10
)

func BenchmarkExtractFramesCLI(b *testing.B) {
	if testing.Short() {
		b.Skip()
	}
	frameReader := new(FramerReaderImpl)
	video := entities.NewVideo(context.Background(), VPath)
	for range b.N {
		for j := range (end-start)/skip + 1 {
			_, err := frameReader.ReadFrameToBufferFps(video.FilePath, start+skip*j, video.FPS)
			require.NoError(b, err)
		}
	}
}

func BenchmarkExtractFramesCLIPipe(b *testing.B) {
	if testing.Short() {
		b.Skip()
	}
	ctx := context.Background()
	frameExtractor := new(FFmpegCLIFrameExtractor)
	video := entities.NewVideo(ctx, VPath)
	for range b.N {
		pr, pw := io.Pipe()
		done := frameExtractor.Start(ctx, video, start, end, skip, pw)
		cnt := 0
		for range frameExtractor.Read(ctx, pr) {
			cnt++
		}
		err := <-done
		require.NoError(b, err)
		assert.Equal(b, (end-start)/skip+1, cnt)
	}
}
