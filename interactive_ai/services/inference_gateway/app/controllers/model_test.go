// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controllers

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"geti.com/iai_core/entities"
	"geti.com/iai_core/logger"
	"geti.com/iai_core/middleware"
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
	"github.com/go-playground/validator/v10"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	mock_controllers "inference_gateway/app/mock/controllers"
)

func TestModelController_Status(t *testing.T) {
	inferenceCtrlMock := mock_controllers.NewMockInferenceController(t)
	fullID := entities.GetFullTestID(t)

	tests := []struct {
		name               string
		giveRequest        string
		setupMocks         func()
		assertExpectations func()
		wantStatusCode     int
		wantJSON           string
	}{
		{
			name: "Ready",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/models/%s/status", fullID.OrganizationID, fullID.WorkspaceID,
				fullID.ProjectID, fullID.TestID),
			setupMocks: func() {
				inferenceCtrlMock.EXPECT().IsModelReady(mock.AnythingOfType("*gin.Context"),
					fullID.ProjectID.String()+"-"+fullID.TestID.String()).Return(true).Once()
			},
			assertExpectations: func() {
				inferenceCtrlMock.AssertExpectations(t)
				inferenceCtrlMock.ExpectedCalls = nil
			},
			wantStatusCode: 200,
			wantJSON:       `{ "model_ready": true }`,
		},
		{
			name: "NotReady",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/models/%s/status", fullID.OrganizationID, fullID.WorkspaceID,
				fullID.ProjectID, fullID.TestID),
			setupMocks: func() {
				inferenceCtrlMock.EXPECT().IsModelReady(mock.AnythingOfType("*gin.Context"),
					fullID.ProjectID.String()+"-"+fullID.TestID.String()).Return(false).Once()
			},
			assertExpectations: func() {
				inferenceCtrlMock.AssertExpectations(t)
				inferenceCtrlMock.ExpectedCalls = nil
			},
			wantStatusCode: 200,
			wantJSON:       `{ "model_ready": false }`,
		},
		{
			name: "InvalidProjectID",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%sextra/models/%s/status", fullID.OrganizationID, fullID.WorkspaceID,
				fullID.ProjectID, fullID.TestID),
			setupMocks: func() {
				inferenceCtrlMock.EXPECT().IsModelReady(mock.AnythingOfType("*gin.Context"),
					fullID.ProjectID.String()+"-"+fullID.TestID.String()).Return(false).Maybe()
			},
			assertExpectations: func() {
				inferenceCtrlMock.AssertNotCalled(t, "IsModelReady")
				inferenceCtrlMock.ExpectedCalls = nil
			},
			wantStatusCode: 400,
		},
		{
			name: "InvalidModelID",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/models/%sextra/status", fullID.OrganizationID, fullID.WorkspaceID,
				fullID.ProjectID, fullID.TestID),
			setupMocks: func() {
				inferenceCtrlMock.EXPECT().IsModelReady(mock.AnythingOfType("*gin.Context"),
					fullID.ProjectID.String()+"-"+fullID.TestID.String()).Return(false).Maybe()
			},
			assertExpectations: func() {
				inferenceCtrlMock.AssertNotCalled(t, "IsModelReady")
				inferenceCtrlMock.ExpectedCalls = nil
			},
			wantStatusCode: 400,
		},
	}

	gin.SetMode(gin.TestMode)
	router := gin.New()
	router.Use(middleware.ErrorHandler())
	modelController := NewModelController(inferenceCtrlMock)

	if v, ok := binding.Validator.Engine().(*validator.Validate); ok {
		if err := v.RegisterValidation("activeOr24Hex", ValidateModelID); err != nil {
			logger.Log().Fatalf("Cannot configure validation: %s", err)
		}
	}

	const basePath = "/api/v1/organizations/:organization_id/workspaces/:workspace_id/projects/:project_id"
	status := router.Group(basePath)
	{
		status.GET("/models/:model_id/status", modelController.Status)
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.setupMocks != nil {
				tt.setupMocks()
			}

			req, _ := http.NewRequest("GET", tt.giveRequest, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			tt.assertExpectations()
			assert.Equal(t, tt.wantStatusCode, resp.Code)
			if tt.wantJSON != "" {
				assert.JSONEq(t, tt.wantJSON, resp.Body.String())
			}
		})
	}
}
