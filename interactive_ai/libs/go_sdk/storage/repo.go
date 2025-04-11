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

package storage

import (
	"context"
	"image"
	"io"

	"geti.com/go_sdk/entities"
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
