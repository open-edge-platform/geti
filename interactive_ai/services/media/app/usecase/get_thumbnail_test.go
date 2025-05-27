// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package usecase

import (
	"context"
	"errors"
	"image"
	"io"
	"os"
	"testing"

	sdkendities "geti.com/iai_core/entities"
	"geti.com/iai_core/storage"
	"geti.com/iai_core/testhelper"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"media/app/service"
)

func readImage(t *testing.T) (*os.File, int64) {
	file, err := os.Open("../test_data/test_jpeg.jpeg")
	require.NoError(t, err)
	stat, err := file.Stat()
	require.NoError(t, err)
	return file, stat.Size()
}

func TestGetOrCreateThumbnail(t *testing.T) {
	mockRepo := storage.NewMockImageRepository(t)
	mockCropper := service.NewMockCropper(t)

	ctx := context.Background()
	fullImageID := testhelper.GetFullImageID(t)
	img := image.NewRGBA(image.Rect(0, 0, 100, 100))
	file, size := readImage(t)
	defer func(file *os.File) {
		err := file.Close()
		if err != nil {
			t.Fatalf("Cannot close file: %s", err)
		}
	}(file)

	tests := []struct {
		name        string
		setupMocks  func()
		wantAsserts func(reader io.ReadCloser, metadata *sdkendities.ObjectMetadata, err error)
	}{
		{
			name: "ThumbnailExists",
			setupMocks: func() {
				mockRepo.EXPECT().
					LoadThumbnailByID(ctx, fullImageID).
					Return(file, sdkendities.NewObjectMetadata(size, "image/jpeg"), nil).
					Once()
			},
			wantAsserts: func(reader io.ReadCloser, metadata *sdkendities.ObjectMetadata, err error) {
				require.NoError(t, err)
				assert.NotNil(t, reader)
				assert.NotNil(t, metadata)
			},
		},
		{
			name: "ThumbnailDoesntExist",
			setupMocks: func() {
				mockRepo.EXPECT().
					LoadThumbnailByID(ctx, fullImageID).
					Return(io.NopCloser(nil), nil, errors.New("not_found")).
					Once()
				mockRepo.EXPECT().
					LoadImageByID(ctx, fullImageID).
					Return(file, sdkendities.NewObjectMetadata(size, "image/jpeg"), nil).
					Once()
				mockRepo.EXPECT().
					SaveThumbnail(ctx, fullImageID, img).
					Return(nil).
					Once()
				mockRepo.EXPECT().
					LoadThumbnailByID(ctx, fullImageID).
					Return(file, sdkendities.NewObjectMetadata(size, "image/jpeg"), nil).
					Once()
				mockCropper.EXPECT().
					CropImage(file, defaultThumbSize, defaultThumbSize).
					Return(img, nil).
					Once()
			},
			wantAsserts: func(reader io.ReadCloser, metadata *sdkendities.ObjectMetadata, err error) {
				require.NoError(t, err)
				assert.NotNil(t, reader)
				assert.NotNil(t, metadata)
			},
		},
		{
			name: "ImageDoesntExist",
			setupMocks: func() {
				mockRepo.EXPECT().
					LoadThumbnailByID(ctx, fullImageID).
					Return(io.NopCloser(nil), nil, errors.New("not_found")).
					Once()
				mockRepo.EXPECT().
					LoadImageByID(ctx, fullImageID).
					Return(io.NopCloser(nil), nil, errors.New("not_found")).
					Once()
			},
			wantAsserts: func(reader io.ReadCloser, metadata *sdkendities.ObjectMetadata, err error) {
				require.ErrorContains(t, err, "Image not found")
				assert.Nil(t, reader)
				assert.Nil(t, metadata)
			},
		},
		{
			name: "CropFailed",
			setupMocks: func() {
				mockRepo.EXPECT().
					LoadThumbnailByID(ctx, fullImageID).
					Return(io.NopCloser(nil), nil, errors.New("not_found")).
					Once()
				mockRepo.EXPECT().
					LoadImageByID(ctx, fullImageID).
					Return(file, sdkendities.NewObjectMetadata(size, "image/jpeg"), nil).
					Once()
				mockCropper.EXPECT().
					CropImage(file, defaultThumbSize, defaultThumbSize).
					Return(img, errors.New("crop_failed")).
					Once()
			},
			wantAsserts: func(reader io.ReadCloser, metadata *sdkendities.ObjectMetadata, err error) {
				require.Error(t, err)
				assert.Nil(t, reader)
				assert.Nil(t, metadata)
			},
		},
		{
			name: "SaveThumbnailFailed",
			setupMocks: func() {
				mockRepo.EXPECT().
					LoadThumbnailByID(ctx, fullImageID).
					Return(io.NopCloser(nil), nil, errors.New("not_found")).
					Once()
				mockRepo.EXPECT().
					LoadImageByID(ctx, fullImageID).
					Return(file, sdkendities.NewObjectMetadata(size, "image/jpeg"), nil).
					Once()
				mockRepo.EXPECT().
					SaveThumbnail(ctx, fullImageID, img).
					Return(errors.New("save_failed")).
					Once()
				mockCropper.EXPECT().
					CropImage(file, defaultThumbSize, defaultThumbSize).
					Return(img, nil).
					Once()
			},
			wantAsserts: func(reader io.ReadCloser, metadata *sdkendities.ObjectMetadata, err error) {
				require.ErrorContains(t, err, "cannot save thumbnail")
				assert.Nil(t, reader)
				assert.Nil(t, metadata)
			},
		},
		{
			name: "ShouldNotGenerateThumbnail",
			setupMocks: func() {
				t.Setenv("FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING", "true")
				mockRepo.EXPECT().
					LoadThumbnailByID(ctx, fullImageID).
					Return(io.NopCloser(nil), nil, errors.New("not_found")).
					Once()
			},
			wantAsserts: func(reader io.ReadCloser, metadata *sdkendities.ObjectMetadata, err error) {
				require.ErrorContains(t, err, "Thumbnail not found")
				assert.Nil(t, reader)
				assert.Nil(t, metadata)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(_ *testing.T) {
			tt.setupMocks()
			uc, _ := NewGetOrCreateImageThumbnail(mockRepo, mockCropper)

			reader, metadata, err := uc.Execute(ctx, fullImageID)
			tt.wantAsserts(reader, metadata, err)

			mockRepo.ExpectedCalls = nil
			mockCropper.ExpectedCalls = nil
		})
	}
}
