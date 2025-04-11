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
	"io"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"geti.com/go_sdk/entities"
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
	for i := 0; i < b.N; i++ {
		for j := 0; j < (end-start)/skip+1; j++ {
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
	for i := 0; i < b.N; i++ {
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
