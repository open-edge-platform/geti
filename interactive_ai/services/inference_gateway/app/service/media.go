// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package service

import (
	"bytes"
	"context"

	sdkentities "geti.com/iai_core/entities"
	"geti.com/iai_core/frames"
	"geti.com/iai_core/logger"
	"geti.com/iai_core/storage"
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

func NewMediaServiceImpl(
	videoRepo storage.VideoRepository,
	imageRepo storage.ImageRepository,
	reader frames.FrameReader,
) *MediaServiceImpl {
	return &MediaServiceImpl{
		videoRepo:   videoRepo,
		imageRepo:   imageRepo,
		frameReader: reader,
	}
}

// GetFrame reads frame specified by index from a video.
func (s *MediaServiceImpl) GetFrame(
	ctx context.Context,
	fullVideoID *sdkentities.FullVideoID,
	frameIndex int,
) (*bytes.Buffer, error) {
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
		if err = imageReader.Close(); err != nil {
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
