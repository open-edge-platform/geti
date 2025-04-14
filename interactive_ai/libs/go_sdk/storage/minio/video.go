// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package minio

import (
	"context"
	"fmt"
	"time"

	"github.com/minio/minio-go/v7"

	"geti.com/go_sdk/entities"
	"geti.com/go_sdk/storage"
	"geti.com/go_sdk/telemetry"
)

const (
	videoExpirationMinutes = 5
	videoObjectType        = "videos"
)

type VideoRepositoryImpl struct {
}

func NewVideoRepositoryImpl() *VideoRepositoryImpl {
	return &VideoRepositoryImpl{}
}

// LoadVideoByID is used to load a video by its ID.
func (repo *VideoRepositoryImpl) LoadVideoByID(ctx context.Context, videoID *entities.FullVideoID) (*entities.Video, error) {
	c, span := telemetry.Tracer().Start(ctx, "load-video")
	defer span.End()
	baseURL := videoID.GetPath()
	videoBucket, bucketErr := storage.GetBucketName(videoObjectType)
	if bucketErr != nil {
		telemetry.RecordError(span, bucketErr)
		return nil, bucketErr
	}

	minioClient, minioErr := getMinioClient(c)
	if minioErr != nil {
		telemetry.RecordError(span, minioErr)
		return nil, minioErr
	}
	objInfo := <-minioClient.ListObjects(ctx, videoBucket, minio.ListObjectsOptions{
		MaxKeys:   1,
		Prefix:    baseURL,
		Recursive: true,
	})
	url := objInfo.Key
	if url == "" {
		err := fmt.Errorf("video with prefix %q not found", baseURL)
		telemetry.RecordError(span, err)
		return nil, err
	}
	objectURL, err := minioClient.PresignedGetObject(c, videoBucket, url, videoExpirationMinutes*time.Minute, nil)
	if err != nil {
		telemetry.RecordError(span, err)
		return nil, err
	}
	return entities.NewVideo(ctx, objectURL.String()), nil
}
