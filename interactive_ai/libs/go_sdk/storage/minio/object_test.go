// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//go:build integration

package minio

import (
	"bytes"
	"context"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	"github.com/google/uuid"
	"github.com/minio/minio-go/v7"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"geti.com/go_sdk/entities"
)

func TestGetObjectByType(t *testing.T) {
	objHandler := ObjectStorageHandlerImpl{}
	ctx := context.Background()
	objectType := "getobject"
	require.NoError(t, os.Setenv("BUCKET_NAME_GETOBJECT", objectType))
	minioClient, err := getMinioClient(ctx)
	require.NoError(t, err)
	err = minioClient.MakeBucket(ctx, objectType, minio.MakeBucketOptions{})
	require.NoError(t, err)
	tests := []struct {
		give       string
		giveObject string
		setupEnv   func(objPath string) *bytes.Buffer
		want       string
	}{
		{
			give:       "NoObjectExists",
			giveObject: "object1",
			want:       "test",
		},
		{
			give:       "ObjectExists",
			giveObject: filepath.Join("organizations", uuid.NewString(), "objects", "object2"),
			setupEnv: func(objPath string) *bytes.Buffer {
				img := image.NewRGBA(image.Rect(0, 0, 100, 100))
				var buffer bytes.Buffer
				require.NoError(t, png.Encode(&buffer, img))
				_, err = minioClient.PutObject(ctx, objectType, objPath+".png",
					bytes.NewReader(buffer.Bytes()), int64(buffer.Len()),
					minio.PutObjectOptions{ContentType: "image/png"})
				require.NoError(t, err)
				return &buffer
			},
			want: "test",
		},
	}

	for _, tt := range tests {
		t.Run(tt.give, func(t *testing.T) {
			var wantBuf *bytes.Buffer
			if tt.setupEnv != nil {
				wantBuf = tt.setupEnv(tt.giveObject)
			}
			obj, metadata, err := objHandler.GetObjectByType(ctx, objectType, tt.giveObject)
			if wantBuf == nil {
				assert.ErrorContains(t, err, fmt.Sprintf("media with prefix %q not found", tt.giveObject))
				return
			}
			assert.Nil(t, err)
			assert.NotNil(t, obj)
			assert.Equal(t, entities.NewObjectMetadata(int64(wantBuf.Len()), "image/png"), metadata, "Size of the object doesn't match")
		})
	}
}

func TestCreateObject(t *testing.T) {
	ctx := context.Background()
	objHandler := ObjectStorageHandlerImpl{}
	buf := bytes.NewBuffer([]byte("mock data"))
	objectType := "createobject"
	require.NoError(t, os.Setenv("BUCKET_NAME_CREATEOBJECT", objectType))
	minioClient, err := getMinioClient(ctx)
	require.NoError(t, err)
	require.NoError(t, minioClient.MakeBucket(ctx, objectType, minio.MakeBucketOptions{}))

	err = objHandler.CreateObject(ctx, objectType, "object", buf, int64(buf.Len()))

	assert.NoError(t, err)
}
