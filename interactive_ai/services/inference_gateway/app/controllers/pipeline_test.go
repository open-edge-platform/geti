// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controllers

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	sdkentities "geti.com/iai_core/entities"
	httperrors "geti.com/iai_core/errors"
	"geti.com/iai_core/logger"
	"geti.com/iai_core/middleware"
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
	"github.com/go-playground/validator/v10"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/suite"

	"inference_gateway/app/entities"
	mockcontrollers "inference_gateway/app/mock/controllers"
	"inference_gateway/app/service"
	"inference_gateway/app/usecase"
)

type PipelineControllerSuite struct {
	suite.Suite
}

func (suite *PipelineControllerSuite) SetupTest() {
	if v, ok := binding.Validator.Engine().(*validator.Validate); ok {
		if err := v.RegisterValidation("activeOr24Hex", ValidateModelID); err != nil {
			logger.Log().Fatalf("Cannot configure validation: %s", err)
		}
	}
}

func (suite *PipelineControllerSuite) TestPipelineController_Status() {
	t := suite.T()
	inferenceCtrlMock := mockcontrollers.NewMockInferenceController(t)
	fullID := sdkentities.GetFullTestID(t)

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
				"/projects/%s/pipelines/%s/status", fullID.OrganizationID, fullID.WorkspaceID,
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
			wantJSON:       `{ "pipeline_ready": true }`,
		},
		{
			name: "ActiveReady",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/pipelines/active/status", fullID.OrganizationID, fullID.WorkspaceID,
				fullID.ProjectID),
			setupMocks: func() {
				inferenceCtrlMock.EXPECT().IsModelReady(mock.AnythingOfType("*gin.Context"),
					fullID.ProjectID.String()+"-active").Return(true).Once()
			},
			assertExpectations: func() {
				inferenceCtrlMock.AssertExpectations(t)
				inferenceCtrlMock.ExpectedCalls = nil
			},
			wantStatusCode: 200,
			wantJSON:       `{ "pipeline_ready": true }`,
		},
		{
			name: "NotReady",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/pipelines/%s/status", fullID.OrganizationID, fullID.WorkspaceID,
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
			wantJSON:       `{ "pipeline_ready": false }`,
		},
		{
			name: "InvalidProjectID",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%sextra/pipelines/%s/status", fullID.OrganizationID, fullID.WorkspaceID,
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
			name: "InvalidPipelineID",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s"+
				"/projects/%s/pipelines/%sextra/status", fullID.OrganizationID, fullID.WorkspaceID,
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
	pipelineCtrl := NewPipelineController(inferenceCtrlMock)

	const basePath = "/api/v1/organizations/:organization_id/workspaces/:workspace_id/projects/:project_id"
	status := router.Group(basePath)
	{
		status.GET("/pipelines/:pipeline_id/status", pipelineCtrl.Status)
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.setupMocks != nil {
				tt.setupMocks()
			}

			req, _ := http.NewRequest(http.MethodGet, tt.giveRequest, nil)
			resp := httptest.NewRecorder()
			req.Context()
			router.ServeHTTP(resp, req)

			tt.assertExpectations()
			assert.Equal(t, tt.wantStatusCode, resp.Code)
			if tt.wantJSON != "" {
				assert.JSONEq(t, tt.wantJSON, resp.Body.String())
			}
		})
	}
}

func (suite *PipelineControllerSuite) TestPipelineController_Infer() {
	t := suite.T()
	inferenceMock := mockcontrollers.NewMockInferenceController(t)

	fullTestID := sdkentities.GetFullTestID(t)
	inferenceRequest := &entities.InferenceRequest{
		OrganizationID: fullTestID.OrganizationID.String(),
		WorkspaceID:    fullTestID.WorkspaceID.String(),
		ProjectID:      fullTestID.ProjectID.String(),
	}

	pipelineCtrl := NewPipelineController(inferenceMock)

	gin.SetMode(gin.TestMode)
	router := gin.New()
	router.Use(middleware.ErrorHandler())

	tests := []struct {
		name        string
		giveRequest string
		setupMocks  func()
		wantBody    string
		wantErrMsg  string
	}{
		{
			name: "PredictActive_OK",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:predict",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID),
			setupMocks: func() {
				inferenceMock.EXPECT().
					Predict(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: "active"}).
					Return(http.StatusOK, []byte(`{ "score": 0.5 }`), nil).
					Once()
			},
		},
		{
			name: "PredictID_OK",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/%s:predict",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID, fullTestID.TestID),
			setupMocks: func() {
				inferenceMock.EXPECT().
					Predict(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: fullTestID.TestID.String()}).
					Return(http.StatusOK, []byte(`{ "score": 0.5 }`), nil).
					Once()
			},
		},
		{
			name: "Predict_Err",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:predict",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID),
			setupMocks: func() {
				inferenceMock.EXPECT().
					Predict(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: "active"}).
					Return(http.StatusBadRequest, nil, httperrors.NewBadRequestError("error")).
					Once()
			},
		},
		{
			name: "Predict_ErrModelNotFound",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:predict",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID),
			setupMocks: func() {
				inferenceMock.EXPECT().
					Predict(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: "active"}).
					Return(http.StatusNotFound, nil, httperrors.NewNotFoundError(service.ErrModelNotFound.Error())).
					Once()
			},
		},
		{
			name: "ExplainActive_OK",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:explain",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID),
			setupMocks: func() {
				inferenceMock.EXPECT().
					Explain(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: "active"}).
					Return([]byte(`{ "score": 0.5 }`), nil).
					Once()
			},
		},
		{
			name: "ExplainID_OK",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/%s:explain",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID, fullTestID.TestID),
			setupMocks: func() {
				inferenceMock.EXPECT().
					Explain(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: fullTestID.TestID.String()}).
					Return([]byte(`{ "score": 0.5 }`), nil).
					Once()
			},
		},
		{
			name: "Explain_Err",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:explain",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID),
			setupMocks: func() {
				inferenceMock.EXPECT().
					Explain(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: "active"}).
					Return(nil, httperrors.NewBadRequestError("error")).
					Once()
			},
		},
		{
			name: "BatchPredictActive_OK",
			giveRequest: fmt.Sprintf(
				"/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:batch_predict",
				fullTestID.OrganizationID,
				fullTestID.WorkspaceID,
				fullTestID.ProjectID,
			),
			setupMocks: func() {
				var batchResp usecase.BatchPredictionJSON
				batchResp.BatchPredictions = append(batchResp.BatchPredictions, []byte(`{"score": 0.5}`))
				inferenceMock.EXPECT().
					BatchPredict(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: "active"}).
					Return(&batchResp, nil).
					Once()
			},
			wantBody: `{"batch_predictions":[{"score":0.5}]}`,
		},
		{
			name: "BatchPredictID_OK",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/%s:batch_predict",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID, fullTestID.TestID),
			setupMocks: func() {
				var batchResp usecase.BatchPredictionJSON
				batchResp.BatchPredictions = append(batchResp.BatchPredictions, []byte(`{"score": 0.5}`))
				inferenceMock.EXPECT().
					BatchPredict(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: fullTestID.TestID.String()}).
					Return(&batchResp, nil).
					Once()
			},
			wantBody: `{"batch_predictions":[{"score":0.5}]}`,
		},
		{
			name: "BatchPredict_Err",
			giveRequest: fmt.Sprintf(
				"/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:batch_predict",
				fullTestID.OrganizationID,
				fullTestID.WorkspaceID,
				fullTestID.ProjectID,
			),
			setupMocks: func() {
				inferenceMock.EXPECT().
					BatchPredict(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: "active"}).
					Return(nil, httperrors.NewBadRequestError("error")).
					Once()
			},
		},
		{
			name: "BatchExplainActive_OK",
			giveRequest: fmt.Sprintf(
				"/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:batch_explain",
				fullTestID.OrganizationID,
				fullTestID.WorkspaceID,
				fullTestID.ProjectID,
			),
			setupMocks: func() {
				var batchResp usecase.BatchExplainJSON
				batchResp.BatchExplain = append(batchResp.BatchExplain, []byte(`{"score": 0.5}`))
				inferenceMock.EXPECT().
					BatchExplain(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: "active"}).
					Return(&batchResp, nil).
					Once()
			},
			wantBody: `{"explanations":[{"score":0.5}]}`,
		},
		{
			name: "BatchExplainID_OK",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/%s:batch_explain",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID, fullTestID.TestID),
			setupMocks: func() {
				var batchResp usecase.BatchExplainJSON
				batchResp.BatchExplain = append(batchResp.BatchExplain, []byte(`{"score": 0.5}`))
				inferenceMock.EXPECT().
					BatchExplain(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: fullTestID.TestID.String()}).
					Return(&batchResp, nil).
					Once()
			},
			wantBody: `{"explanations":[{"score":0.5}]}`,
		},
		{
			name: "BatchExplain_Err",
			giveRequest: fmt.Sprintf(
				"/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:batch_explain",
				fullTestID.OrganizationID,
				fullTestID.WorkspaceID,
				fullTestID.ProjectID,
			),
			setupMocks: func() {
				var batchResp usecase.BatchExplainJSON
				batchResp.BatchExplain = append(batchResp.BatchExplain, []byte(`{"score": 0.5}`))
				inferenceMock.EXPECT().
					BatchExplain(mock.AnythingOfType("*gin.Context"), inferenceRequest, sdkentities.ID{ID: "active"}).
					Return(nil, httperrors.NewBadRequestError("error")).
					Once()
			},
		},
		{
			name: "Unknown",
			giveRequest: fmt.Sprintf("/api/v1/organizations/%s/workspaces/%s/projects/%s/pipelines/active:unknown",
				fullTestID.OrganizationID, fullTestID.WorkspaceID, fullTestID.ProjectID),
			wantErrMsg: fmt.Sprintf(
				"Action `unknown` is not a valid action. Choose one of %s",
				entities.GetSupportedActions(),
			),
		},
	}

	pipelines := router.Group(
		"/api/v1/organizations/:organization_id/workspaces/:workspace_id/projects/:project_id/pipelines/:pipeline_id",
	)
	{
		pipelines.POST("", pipelineCtrl.Infer)
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.setupMocks != nil {
				tt.setupMocks()
			}

			req, _ := http.NewRequest(http.MethodPost, tt.giveRequest, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			switch resp.Code {
			case http.StatusNoContent:
				assert.Equal(t, "Predict_ErrModelNotFound", tt.name)
			case http.StatusOK:
				if tt.wantBody != "" {
					assert.Equal(t, tt.wantBody, resp.Body.String())
				} else {
					assert.Equal(t, `{ "score": 0.5 }`, resp.Body.String())
				}
			default:
				if tt.wantErrMsg != "" {
					assert.Contains(t, resp.Body.String(), tt.wantErrMsg)
				} else {
					assert.Contains(t, resp.Body.String(), "error")
				}
			}

			inferenceMock.ExpectedCalls = nil
			inferenceMock.Calls = nil
		})
	}
}

func TestPipelineController(t *testing.T) {
	suite.Run(t, new(PipelineControllerSuite))
}
