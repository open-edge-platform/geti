// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package service

import (
	"bytes"
	"context"
	"errors"
	"io"
	"strings"
	"testing"

	sdkentities "geti.com/iai_core/entities"
	mockframes "geti.com/iai_core/mock/frames"
	mockstorage "geti.com/iai_core/mock/storage"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMediaService(t *testing.T) {
	videoRepoMock := mockstorage.NewMockVideoRepository(t)
	imageRepoMock := mockstorage.NewMockImageRepository(t)
	frameReaderMock := mockframes.NewMockFrameReader(t)

	ctx := context.Background()
	fullImageID := sdkentities.GetFullImageID(t)
	fullVideoID := sdkentities.GetFullVideoID(t)
	mediaSrv := NewMediaServiceImpl(videoRepoMock, imageRepoMock, frameReaderMock)

	tests := []struct {
		name            string
		setupMocks      func()
		actionAndAssert func()
	}{
		{
			name: "GetImage_OK",
			setupMocks: func() {
				reader := io.NopCloser(strings.NewReader("test"))
				imageRepoMock.EXPECT().
					LoadImageByID(ctx, fullImageID).
					Return(reader, nil, nil).
					Once()
			},
			actionAndAssert: func() {
				buf, err := mediaSrv.GetImage(ctx, fullImageID)
				require.NoError(t, err)
				assert.Equal(t, "test", buf.String())
			},
		},
		{
			name: "GetImage_Err",
			setupMocks: func() {
				imageRepoMock.EXPECT().
					LoadImageByID(ctx, fullImageID).
					Return(nil, nil, errors.New("error")).
					Once()
			},
			actionAndAssert: func() {
				buf, err := mediaSrv.GetImage(ctx, fullImageID)
				assert.Nil(t, buf)
				assert.Error(t, err)
			},
		},
		{
			name: "GetFrame_OK",
			setupMocks: func() {
				video := &sdkentities.Video{
					FilePath: "somepath",
					FPS:      25,
				}
				videoRepoMock.EXPECT().
					LoadVideoByID(ctx, fullVideoID).
					Return(video, nil).
					Once()
				frameReaderMock.EXPECT().
					ReadFrameToBufferFps("somepath", 1, float64(25)).
					Return(bytes.NewBufferString("test"), nil).
					Once()
			},
			actionAndAssert: func() {
				buf, err := mediaSrv.GetFrame(ctx, fullVideoID, 1)
				require.NoError(t, err)
				assert.NotNil(t, buf)
			},
		},
		{
			name: "GetFrame_ErrLoad",
			setupMocks: func() {
				videoRepoMock.EXPECT().
					LoadVideoByID(ctx, fullVideoID).
					Return(nil, errors.New("error")).
					Once()
			},
			actionAndAssert: func() {
				buf, err := mediaSrv.GetFrame(ctx, fullVideoID, 1)
				assert.Nil(t, buf)
				assert.Error(t, err)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(_ *testing.T) {
			tt.setupMocks()

			tt.actionAndAssert()

			imageRepoMock.ExpectedCalls = nil
			imageRepoMock.Calls = nil
			videoRepoMock.ExpectedCalls = nil
			videoRepoMock.Calls = nil
			frameReaderMock.ExpectedCalls = nil
			frameReaderMock.Calls = nil
		})
	}
}
