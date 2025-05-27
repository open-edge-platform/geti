// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package usecase

import (
	"context"
	"fmt"
	"io"

	sdkentities "geti.com/iai_core/entities"
	"geti.com/iai_core/logger"
	"geti.com/iai_core/storage"
	"github.com/caarlos0/env/v11"

	"media/app/service"
)

const defaultThumbSize = 256

type NotFoundError struct {
	Message string
}

type EnvsConfig struct {
	AsynchronousMediaPreprocessing bool `env:"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING" envDefault:"false"`
}

func (e *NotFoundError) Error() string {
	return e.Message
}

type IGetOrCreateThumbnail interface {
	Execute(ctx context.Context, imageID *sdkentities.FullImageID) (io.ReadCloser, *sdkentities.ObjectMetadata, error)
}

type GetOrCreateThumbnail struct {
	imageRepo storage.ImageRepository
	cropper   service.Cropper
	cfg       EnvsConfig
}

func NewGetOrCreateImageThumbnail(
	imageRepo storage.ImageRepository,
	cropper service.Cropper,
) (*GetOrCreateThumbnail, error) {
	cfg := EnvsConfig{}
	if err := env.Parse(&cfg); err != nil {
		return nil, fmt.Errorf("NewGetOrCreateImageThumbnail error: %w", err)
	}
	return &GetOrCreateThumbnail{
		imageRepo: imageRepo,
		cropper:   cropper,
		cfg:       cfg,
	}, nil
}

// Execute generates a thumbnail for the image with the specified ID and saves it to the storage.
// The method is agnostic to S3 being enabled or disabled.
func (uc *GetOrCreateThumbnail) Execute(
	ctx context.Context,
	imageID *sdkentities.FullImageID,
) (io.ReadCloser, *sdkentities.ObjectMetadata, error) {
	thumbnail, metadata, thumbErr := uc.imageRepo.LoadThumbnailByID(ctx, imageID)
	if thumbErr != nil && uc.cfg.AsynchronousMediaPreprocessing {
		return nil, nil, &NotFoundError{"Thumbnail not found"}
	}
	if thumbErr != nil {
		logger.TracingLog(ctx).Infof(
			"Thumbnail for Image with ID %s does not yet exist. Attempting to generate one.", imageID)
		reader, _, err := uc.imageRepo.LoadImageByID(ctx, imageID)
		if err != nil {
			return nil, nil, &NotFoundError{"Image not found"}
		}
		croppedImage, err := uc.cropper.CropImage(reader, defaultThumbSize, defaultThumbSize)
		if err != nil {
			return nil, nil, err
		}
		if err = uc.imageRepo.SaveThumbnail(ctx, imageID, croppedImage); err != nil {
			return nil, nil, fmt.Errorf("cannot save thumbnail: %w", err)
		}
		logger.TracingLog(ctx).Infof("Successfully generated thumbnail for Image with ID %s", imageID)
		thumbnail, metadata, err = uc.imageRepo.LoadThumbnailByID(ctx, imageID)
		if err != nil {
			return nil, nil, &NotFoundError{"Thumbnail not found"}
		}
	}
	return thumbnail, metadata, nil
}
