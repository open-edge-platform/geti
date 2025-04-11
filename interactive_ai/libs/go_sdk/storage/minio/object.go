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

package minio

import (
	"context"
	"errors"
	"fmt"
	"io"

	"github.com/minio/minio-go/v7"

	"geti.com/go_sdk/entities"
	"geti.com/go_sdk/storage"
)

type ObjectStorageHandlerImpl struct{}

// GetObjectByType is a function that retrieves an object from a bucket based on the provided object name and type.
// It returns an io.Reader, the size of the object, and an error if any.
// The function will make a minio index lookup with minio.ListObjects API with object name without extension passed as a prefix and limit 1.
// If object exists, the reader will be instantiated with minio.GetObject and will be ready for the further retrieval operations.
func (h *ObjectStorageHandlerImpl) GetObjectByType(ctx context.Context, objectType, objectName string) (io.ReadCloser, *entities.ObjectMetadata, error) {
	bucketName, err := storage.GetBucketName(objectType)
	if err != nil {
		return nil, nil, err
	}

	minioClient, minioErr := getMinioClient(ctx)
	if minioErr != nil {
		return nil, nil, minioErr
	}
	objInfo := <-minioClient.ListObjects(ctx, bucketName, minio.ListObjectsOptions{
		MaxKeys:   1,
		Prefix:    objectName,
		Recursive: true,
	})
	url := objInfo.Key
	if url == "" {
		return nil, nil, fmt.Errorf("media with prefix %q not found", objectName)
	}
	object, err := minioClient.GetObject(ctx, bucketName, url, minio.GetObjectOptions{})
	if err != nil {
		var minErr minio.ErrorResponse
		if errors.As(err, &minErr) && minErr.Code == "NoSuchKey" {
			return nil, nil, fmt.Errorf("media with prefix %q not found", objectName)
		}
	}

	stats, err := object.Stat()
	if err != nil {
		return nil, nil, err
	}

	return object, entities.NewObjectMetadata(stats.Size, stats.ContentType), err
}

// CreateObject uploads a new object to a bucket in MinIO storage.
// It returns an error if the bucket for specified type doesn't exist or object creation fails, otherwise nil.
func (h *ObjectStorageHandlerImpl) CreateObject(ctx context.Context, objectType, objectName string, reader io.Reader, objectSize int64) error {
	bucketName, err := storage.GetBucketName(objectType)
	if err != nil {
		return err
	}
	minioClient, minioErr := getMinioClient(ctx)
	if minioErr != nil {
		return minioErr
	}
	if _, err := minioClient.PutObject(ctx, bucketName, objectName, reader, objectSize, minio.PutObjectOptions{}); err != nil {
		return err
	}
	return nil
}
