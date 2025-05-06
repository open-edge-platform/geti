// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package storage

import (
	"context"
	"image"
	"io"

	"geti.com/iai_core/entities"
)

// ObjectStorageHandler defines the interface for operations related to managing objects within storage buckets.
type ObjectStorageHandler interface {
	GetObjectByType(ctx context.Context, objectType, objectName string) (io.ReadCloser, *entities.ObjectMetadata, error)
	CreateObject(ctx context.Context, objectType, objectName string, reader io.Reader, objectSize int64) error
}

// ImageRepository defines the interface for operations related to image storage and retrieval.
type ImageRepository interface {
	LoadImageByID(ctx context.Context, imageID *entities.FullImageID) (io.ReadCloser, *entities.ObjectMetadata, error)
	LoadThumbnailByID(ctx context.Context, imageID *entities.FullImageID) (io.ReadCloser, *entities.ObjectMetadata, error)
	SaveThumbnail(ctx context.Context, imageID *entities.FullImageID, thumbnail image.Image) error
}

// VideoRepository defines the interface for operations related to video retrieval.
type VideoRepository interface {
	LoadVideoByID(ctx context.Context, videoID *entities.FullVideoID) (*entities.Video, error)
}
