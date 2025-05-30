// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package minio

import (
	"bytes"
	"context"
	"image"
	"image/jpeg"
	"io"

	"geti.com/iai_core/entities"
	"geti.com/iai_core/logger"
	"geti.com/iai_core/storage"
	"geti.com/iai_core/telemetry"
)

const (
	imageType     = "images"
	thumbnailType = "thumbnails"
)

type ImageRepositoryImpl struct {
	storage.ObjectStorageHandler
}

func NewImageRepositoryImpl() *ImageRepositoryImpl {
	return &ImageRepositoryImpl{
		ObjectStorageHandler: new(ObjectStorageHandlerImpl),
	}
}

// LoadImageByID retrieves an image from MinIO storage.
// It returns:
// - An io.ReadCloser that allows reading the thumbnail image data.
// - A metadata that contains the size and the content type of the image.
// - An error if the thumbnail retrieval fails, otherwise nil.
func (repo *ImageRepositoryImpl) LoadImageByID(
	ctx context.Context,
	imageID *entities.FullImageID,
) (io.ReadCloser, *entities.ObjectMetadata, error) {
	c, span := telemetry.Tracer().Start(ctx, "load-image")
	defer span.End()
	reader, metadata, err := repo.GetObjectByType(c, imageType, imageID.GetPath())
	if err != nil {
		telemetry.RecordError(span, err)
		return nil, nil, err
	}
	return reader, metadata, nil
}

// LoadThumbnailByID retrieves a thumbnail image from MinIO storage.
// It returns:
// - An io.ReadCloser that allows reading the thumbnail image data.
// - A metadata that contains the size and the content type of the thumbnail image.
// - An error if the thumbnail retrieval fails, otherwise nil.
func (repo *ImageRepositoryImpl) LoadThumbnailByID(
	ctx context.Context,
	imageID *entities.FullImageID,
) (io.ReadCloser, *entities.ObjectMetadata, error) {
	c, span := telemetry.Tracer().Start(ctx, "load-thumbnail")
	defer span.End()
	reader, metadata, err := repo.GetObjectByType(c, thumbnailType, imageID.GetThumbnailPath())
	if err != nil {
		telemetry.RecordError(span, err)
		return nil, nil, err
	}
	return reader, metadata, nil
}

// SaveThumbnail uploads a thumbnail image in MinIO storage.
// It returns an error if the thumbnail upload fails, otherwise nil.
func (repo *ImageRepositoryImpl) SaveThumbnail(
	ctx context.Context,
	imageID *entities.FullImageID,
	thumbnail image.Image,
) error {
	c, span := telemetry.Tracer().Start(ctx, "save-thumbnail")
	defer span.End()
	thumbName := imageID.GetThumbnailPath()
	buff := new(bytes.Buffer)
	err := jpeg.Encode(buff, thumbnail, nil)
	if err != nil {
		telemetry.RecordError(span, err)
		return err
	}
	logger.TracingLog(c).Infof("Creating thumbnail %s", thumbName)
	err = repo.CreateObject(c, thumbnailType, thumbName, buff, int64(buff.Len()))
	if err != nil {
		telemetry.RecordError(span, err)
		return err
	}
	logger.TracingLog(c).Infof("Successfully saved image at url %s to S3", thumbName)
	return nil
}
