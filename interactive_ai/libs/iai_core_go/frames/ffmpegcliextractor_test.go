// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//go:build integration

package frames

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"testing"

	"github.com/stretchr/testify/suite"
	"github.com/testcontainers/testcontainers-go"

	"geti.com/iai_core/entities"
	"geti.com/iai_core/testhelper"
)

type FFmpegFrameExtractorTestSuite struct {
	minioContainer testcontainers.Container
	video          *entities.Video

	suite.Suite
}

// SetupSuite starts a Minio container and uploads a video file to it.
// The process includes the following steps:
// 1. Initialize and run a Minio container for object storage.
// 2. Upload the video file to the Minio storage and generates presigned URL.
// This setup is essential for testing the frame extraction functionality from a video stored in Minio.
func (suite *FFmpegFrameExtractorTestSuite) SetupSuite() {
	ctx := context.Background()
	container, err := testhelper.StartMinioContainer(ctx)
	if err != nil {
		suite.Fail("Cannot start minio container: %v", err)
	}
	suite.minioContainer = container
	fullVideoID := entities.GetFullVideoID(suite.T())
	videoURL, err := testhelper.PrepareTestVideo(ctx, fullVideoID,
		"../test_data/test_mp4.mp4")
	if err != nil {
		suite.Fail("Cannot generate videoID")
	}
	suite.video = entities.NewVideo(ctx, videoURL)
}

func (suite *FFmpegFrameExtractorTestSuite) TearDownSuite() {
	if err := testhelper.StopMinioContainer(context.Background(), suite.minioContainer); err != nil {
		suite.Fail("Cannot stop minio container")
	}
}

// TestFrameExtractor verifies the functionality of the frame extraction process from a video uploaded to Minio using a presigned URL.
// The test performs the following checks:
// 1. Ensures that each frame extracted and pushed to a channel is a valid JPEG by checking the presence of JPEG start (0xFF,0xD8) and end (0xFF,0xD9) markers.
// 2. Asserts that the total number of frames extracted matches the expected count.
// The validation of frames involves reading from the channel, verifying the JPEG markers, counting the frames and checking
// that there is no error returned by ffmpeg process
func (suite *FFmpegFrameExtractorTestSuite) TestFrameExtractor() {
	ctx := context.Background()
	pr, pw := io.Pipe()
	frameExtractor := new(FFmpegCLIFrameExtractor)
	start, end, skip := 30, 90, 10
	wantTotal := (end-start)/skip + 1
	done := frameExtractor.Start(ctx, suite.video, start, end, skip, pw)

	frameCount := 0
	for frame := range frameExtractor.Read(ctx, pr) {
		frameCount++
		suite.True(bytes.HasPrefix(frame.Data, []byte{0xFF, 0xD8}), "JPEG start marker not found")
		suite.True(bytes.HasSuffix(frame.Data, []byte{0xFF, 0xD9}), "JPEG end marker not found")
	}
	err := <-done
	suite.Equal(wantTotal, frameCount, fmt.Sprintf("number of extracted frames should be %d", wantTotal))
	suite.NoError(err, fmt.Sprintf("Error extracting frames: %v", err))
}

func TestFFmpegFrameExtractorTestSuite(t *testing.T) {
	suite.Run(t, new(FFmpegFrameExtractorTestSuite))
}
