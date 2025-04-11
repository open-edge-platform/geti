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
	"context"

	sdkentities "geti.com/go_sdk/entities"
	"geti.com/go_sdk/frames"
	"geti.com/go_sdk/logger"
	"geti.com/go_sdk/storage"
)

type MediaService interface {
	GetFrame(ctx context.Context, fullVideoID *sdkentities.FullVideoID, frameIndex int) (*bytes.Buffer, error)
	GetImage(ctx context.Context, fullImageID *sdkentities.FullImageID) (*bytes.Buffer, error)
}

type MediaServiceImpl struct {
	videoRepo   storage.VideoRepository
	imageRepo   storage.ImageRepository
	frameReader frames.FrameReader
}

func NewMediaServiceImpl(videoRepo storage.VideoRepository, imageRepo storage.ImageRepository, reader frames.FrameReader) *MediaServiceImpl {
	return &MediaServiceImpl{
		videoRepo:   videoRepo,
		imageRepo:   imageRepo,
		frameReader: reader,
	}
}

// GetFrame reads frame specified by index from a video
func (s *MediaServiceImpl) GetFrame(ctx context.Context, fullVideoID *sdkentities.FullVideoID, frameIndex int) (*bytes.Buffer, error) {
	video, loadErr := s.videoRepo.LoadVideoByID(ctx, fullVideoID)
	if loadErr != nil {
		return nil, loadErr
	}

	return s.frameReader.ReadFrameToBufferFps(video.FilePath, frameIndex, video.FPS)
}

func (s *MediaServiceImpl) GetImage(ctx context.Context, fullImageID *sdkentities.FullImageID) (*bytes.Buffer, error) {
	imageReader, _, err := s.imageRepo.LoadImageByID(ctx, fullImageID)
	if err != nil {
		return nil, err
	}
	defer func() {
		if err := imageReader.Close(); err != nil {
			logger.TracingLog(ctx).Errorf("Error closing imageReader: %s", err)
		}
	}()
	var buf bytes.Buffer
	_, readErr := buf.ReadFrom(imageReader)
	if readErr != nil {
		return nil, readErr
	}
	return &buf, nil
}
