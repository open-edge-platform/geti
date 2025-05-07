// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package testhelper

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"

	"geti.com/iai_core/entities"
)

const (
	bucketName      = "videos"
	expireInMinutes = 1
)

// PrepareTestVideo creates a new bucket in the Minio storage, uploads a video file to this bucket,
// and generates a presigned URL for accessing the uploaded video. The presigned URL is valid for 1 minute.
func PrepareTestVideo(ctx context.Context, videoID *entities.FullVideoID, videoPath string) (string, error) {

	client, err := minio.New(os.Getenv("S3_HOST"), &minio.Options{
		Creds:  credentials.NewStaticV4(os.Getenv("S3_ACCESS_KEY"), os.Getenv("S3_SECRET_KEY"), ""),
		Secure: false,
	})
	if err != nil {
		return "", fmt.Errorf("cannot instantiate minioClient: %s", err)
	}
	err = client.MakeBucket(ctx, bucketName, minio.MakeBucketOptions{})
	if err != nil {
		return "", fmt.Errorf("cannot create a new bucket: %s", err)
	}
	_ = os.Setenv("BUCKET_NAME_VIDEOS", bucketName)
	objectName := videoID.GetPath() + ".mp4"
	_, err = client.FPutObject(ctx, bucketName, objectName, videoPath, minio.PutObjectOptions{ContentType: "video/mp4"})
	if err != nil {
		return "", fmt.Errorf("cannot create object: %s", err)
	}
	url, err := client.PresignedGetObject(ctx, bucketName, objectName, expireInMinutes*time.Minute, nil)
	if err != nil {
		return "", fmt.Errorf("cannot generate presigned url: %s", err)
	}
	return url.String(), nil
}
