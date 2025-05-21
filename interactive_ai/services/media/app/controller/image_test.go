// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controller

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	sdkendities "geti.com/iai_core/entities"
	"geti.com/iai_core/middleware"
	mockstorage "geti.com/iai_core/mock/storage"
	"geti.com/iai_core/testhelper"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"media/app/usecase"
)

func readImage(t *testing.T) *os.File {
	file, err := os.Open("../test_data/test_jpeg.jpeg")
	assert.NoError(t, err)
	return file
}

func TestImageController(t *testing.T) {
	fullImageID := testhelper.GetFullImageID(t)

	ctx := context.Background()
	mockImageRepo := mockstorage.NewMockImageRepository(t)
	mockGetThumbUC := usecase.NewMockIGetOrCreateThumbnail(t)

	tests := []struct {
		name                  string
		giveRequest           string
		setupMocks            func()
		assertExpectations    func()
		wantStatusCode        int
		wantContentTypeHeader string
	}{
		{
			name: "GetImage_OK",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/datasets/%s/media/images/%s/display/full", fullImageID.OrganizationID, fullImageID.WorkspaceID,
				fullImageID.ProjectID, fullImageID.DatasetID, fullImageID.ImageID),
			setupMocks: func() {
				mockImageRepo.EXPECT().
					LoadImageByID(ctx, fullImageID).
					Return(readImage(t), sdkendities.NewObjectMetadata(0, "image/jpeg"), nil).
					Once()
			},
			wantStatusCode:        200,
			wantContentTypeHeader: "image/jpeg",
		},
		{
			name: "GetImage_BadRequest_LongerImageID",
			giveRequest: "/api/v1/organizations/ba2b9a3d-b77a-4dac-a9de-e05315ffec97/workspaces/a8fe4ded-31ce-42bc-8586-6b2c6635833f/" +
				"projects/65c497ad388f69938228908b/datasets/65c497ad388f699382289091/media/images/65c4987280b55559653d79257177/display/full",
			setupMocks: func() {
				mockImageRepo.EXPECT().
					LoadImageByID(ctx, fullImageID).
					Return(readImage(t), nil, nil).
					Maybe()
			},
			assertExpectations: func() {
				mockImageRepo.AssertNotCalled(t, "LoadImageByID")
			},
			wantStatusCode: 400,
		},
		{
			name: "GetImage_NotFound",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/datasets/%s/media/images/%s/display/full", fullImageID.OrganizationID, fullImageID.WorkspaceID,
				fullImageID.ProjectID, fullImageID.DatasetID, fullImageID.ImageID),
			setupMocks: func() {
				mockImageRepo.EXPECT().
					LoadImageByID(ctx, fullImageID).
					Return(io.NopCloser(nil), nil, errors.New("cannot read image")).
					Once()
			},
			wantStatusCode: 404,
		},
		{
			name: "GetThumb_OK",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/datasets/%s/media/images/%s/display/thumb", fullImageID.OrganizationID, fullImageID.WorkspaceID,
				fullImageID.ProjectID, fullImageID.DatasetID, fullImageID.ImageID),
			setupMocks: func() {
				mockGetThumbUC.EXPECT().
					Execute(ctx, fullImageID).
					Return(readImage(t), sdkendities.NewObjectMetadata(0, "image/jpeg"), nil).
					Once()
			},
			wantStatusCode:        200,
			wantContentTypeHeader: "image/jpeg",
		},
		{
			name: "GetThumb_BadRequest_InvalidOrgID",
			giveRequest: "/api/v1/organizations/ba2b9a3d-b77a-4dac-a9de-e05315ffec97-b88/workspaces/a8fe4ded-31ce-42bc-8586-6b2c6635833f/" +
				"projects/65c497ad388f69938228908b/datasets/65c497ad388f699382289091/media/images/65c4987280b55559653d7925/display/thumb",
			setupMocks: func() {
				mockGetThumbUC.EXPECT().
					Execute(ctx, fullImageID).
					Return(readImage(t), sdkendities.NewObjectMetadata(0, "image/jpeg"), nil).
					Maybe()
			},
			assertExpectations: func() {
				mockGetThumbUC.AssertNotCalled(t, "Execute")
			},
			wantStatusCode: 400,
		},
		{
			name: "GetThumb_NotFound",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/datasets/%s/media/images/%s/display/thumb", fullImageID.OrganizationID, fullImageID.WorkspaceID,
				fullImageID.ProjectID, fullImageID.DatasetID, fullImageID.ImageID),
			setupMocks: func() {
				mockGetThumbUC.EXPECT().
					Execute(ctx, fullImageID).
					Return(io.NopCloser(nil), nil, &usecase.NotFoundError{Message: "not_found"}).
					Once()
			},
			wantStatusCode: 404,
		},
		{
			name: "GetThumb_InternalError",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/datasets/%s/media/images/%s/display/thumb", fullImageID.OrganizationID, fullImageID.WorkspaceID,
				fullImageID.ProjectID, fullImageID.DatasetID, fullImageID.ImageID),
			setupMocks: func() {
				mockGetThumbUC.EXPECT().
					Execute(ctx, fullImageID).
					Return(io.NopCloser(nil), nil, errors.New("error")).
					Once()
			},
			wantStatusCode: 500,
		},
	}

	gin.SetMode(gin.TestMode)
	router := gin.Default()
	router.Use(middleware.ErrorHandler())

	imageController := NewImageController(mockGetThumbUC, mockImageRepo)
	images := router.Group("/api/v1/organizations/:organization_id/workspaces/:workspace_id/projects/:project_id/" +
		"datasets/:dataset_id/media/images/:image_id/display")
	{
		images.GET("/full", imageController.GetImage)
		images.GET("/thumb", imageController.GetThumbnail)
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.setupMocks != nil {
				tt.setupMocks()
			}

			req, _ := http.NewRequest(http.MethodGet, tt.giveRequest, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			if tt.assertExpectations != nil {
				tt.assertExpectations()
			}
			assert.Equal(t, tt.wantStatusCode, resp.Code)
			if tt.wantContentTypeHeader != "" {
				assert.Equal(t, tt.wantContentTypeHeader, resp.Header().Get("Content-Type"))
			}

			mockImageRepo.ExpectedCalls = nil
			mockGetThumbUC.ExpectedCalls = nil
		})
	}
}
