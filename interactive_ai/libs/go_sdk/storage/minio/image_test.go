// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//go:build integration

package minio

import (
	"bytes"
	"context"
	"image"
	"image/jpeg"
	"io"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"

	"geti.com/go_sdk/entities"
	mockstorage "geti.com/go_sdk/mock/storage"
)

func TestLoad(t *testing.T) {

	fullImageID := entities.GetFullImageID(t)
	ctx := context.Background()
	mockObjStorageHandler := mockstorage.NewMockObjectStorageHandler(t)
	imageRepo := &ImageRepositoryImpl{ObjectStorageHandler: mockObjStorageHandler}

	tests := []struct {
		name       string
		setupMocks func()
		action     func() (io.ReadCloser, *entities.ObjectMetadata, error)
	}{
		{
			name: "Image",
			setupMocks: func() {
				require.NoError(t, os.Setenv("BUCKET_NAME_IMAGES", imageType))

				mockObjStorageHandler.EXPECT().
					GetObjectByType(mock.AnythingOfType("*context.valueCtx"), imageType, fullImageID.GetPath()).
					Return(io.NopCloser(nil), &entities.ObjectMetadata{Size: 0}, nil).
					Once()
			},
			action: func() (io.ReadCloser, *entities.ObjectMetadata, error) {
				return imageRepo.LoadImageByID(ctx, fullImageID)
			},
		},

		{
			name: "Thumbnail",
			setupMocks: func() {
				require.NoError(t, os.Setenv("BUCKET_NAME_THUMBNAILS", thumbnailType))

				mockObjStorageHandler.EXPECT().
					GetObjectByType(mock.AnythingOfType("*context.valueCtx"), thumbnailType, fullImageID.GetThumbnailPath()).
					Return(io.NopCloser(nil), &entities.ObjectMetadata{Size: 0}, nil).
					Once()
			},
			action: func() (io.ReadCloser, *entities.ObjectMetadata, error) {
				return imageRepo.LoadThumbnailByID(ctx, fullImageID)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(_ *testing.T) {
			if tt.setupMocks != nil {
				tt.setupMocks()
			}

			obj, metadata, err := tt.action()

			mockObjStorageHandler.AssertExpectations(t)
			assert.NoError(t, err)
			assert.NotNil(t, metadata)
			assert.Equal(t, obj, io.NopCloser(nil))

			mockObjStorageHandler.ExpectedCalls = nil
			mockObjStorageHandler.Calls = nil
		})
	}
}

func TestSave(t *testing.T) {

	fullImageID := entities.GetFullImageID(t)
	ctx := context.Background()
	media := image.NewRGBA(image.Rect(0, 0, 1, 1))
	buf := new(bytes.Buffer)
	require.NoError(t, jpeg.Encode(buf, media, nil))
	require.NoError(t, os.Setenv("BUCKET_NAME_THUMBNAILS", thumbnailType))

	mockObjStorageHandler := mockstorage.NewMockObjectStorageHandler(t)
	imageRepo := &ImageRepositoryImpl{ObjectStorageHandler: mockObjStorageHandler}

	mockObjStorageHandler.EXPECT().
		CreateObject(mock.AnythingOfType("*context.valueCtx"), thumbnailType, fullImageID.GetThumbnailPath(), buf, int64(buf.Len())).
		Return(nil).
		Once()

	err := imageRepo.SaveThumbnail(ctx, fullImageID, media)

	mockObjStorageHandler.AssertExpectations(t)
	assert.NoError(t, err)
}
