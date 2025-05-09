// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controllers

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	sdkentities "geti.com/iai_core/entities"
	httperrors "geti.com/iai_core/errors"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"inference_gateway/app/entities"
	mockcontrollers "inference_gateway/app/mock/controllers"
	mockservice "inference_gateway/app/mock/service"
	mockusecase "inference_gateway/app/mock/usecase"
	"inference_gateway/app/usecase"
)

func TestInferenceController_InferOne(t *testing.T) {
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/path", nil)

	modelAccessMock := mockservice.NewMockModelAccessService(t)
	cacheMock := mockservice.NewMockCacheService(t)
	predictMock := mockusecase.NewMockInfer[usecase.BatchPredictionJSON](t)
	explainMock := mockusecase.NewMockInfer[usecase.BatchExplainJSON](t)
	requestHandlerMock := mockcontrollers.NewMockRequestHandler(t)

	entityID := sdkentities.ID{ID: "active"}
	fullVideoID := sdkentities.GetFullVideoID(t)
	inferenceRequest := &entities.InferenceRequest{
		OrganizationID: fullVideoID.OrganizationID.String(),
		WorkspaceID:    fullVideoID.WorkspaceID.String(),
		ProjectID:      fullVideoID.ProjectID.String(),
	}
	requestData := &entities.PredictionRequestData{
		OrganizationID: fullVideoID.OrganizationID,
		WorkspaceID:    fullVideoID.WorkspaceID,
		ProjectID:      fullVideoID.ProjectID,
		ModelID:        entityID,
		UseCache:       entities.Always,
	}

	inferenceCtrl := NewInferenceControllerImpl(modelAccessMock, cacheMock, requestHandlerMock, predictMock, explainMock)

	tests := []struct {
		name            string
		setupMocks      func()
		actionAndAssert func(t *testing.T)
	}{
		{
			name: "Predict_Cached200",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				cacheMock.EXPECT().
					Get(c.Request.Context(), requestData).
					Return(http.StatusOK, []byte("cached"), true).
					Once()

				predictMock.EXPECT().
					One(c.Request.Context(), requestData).
					Return("predictions", nil).
					Maybe()
			},
			actionAndAssert: func(t *testing.T) {
				statusCode, result, err := inferenceCtrl.Predict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Equal(t, http.StatusOK, statusCode)
				assert.Nil(t, err)
				assert.Equal(t, []byte("cached"), result)

				predictMock.AssertNotCalled(t, "One", c.Request.Context(), requestData)

			},
		},
		{
			name: "Predict_Cached204",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				cacheMock.EXPECT().
					Get(c.Request.Context(), requestData).
					Return(http.StatusNoContent, []byte("no prediction found"), true).
					Once()

				predictMock.EXPECT().
					One(c.Request.Context(), requestData).
					Return("predictions", nil).
					Maybe()
			},
			actionAndAssert: func(t *testing.T) {
				statusCode, result, err := inferenceCtrl.Predict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Equal(t, http.StatusNoContent, statusCode)
				assert.Nil(t, err)
				assert.Equal(t, []byte("no prediction found"), result)

				predictMock.AssertNotCalled(t, "One", c.Request.Context(), requestData)

			},
		},
		{
			name: "Predict_NoCached",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				cacheMock.EXPECT().
					Get(c.Request.Context(), requestData).
					Return(200, []byte("cached"), false).
					Once()

				predictMock.EXPECT().
					One(c.Request.Context(), requestData).
					Return("{\"predictions\":[1,2]}", nil).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				statusCode, result, err := inferenceCtrl.Predict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Equal(t, http.StatusOK, statusCode)
				assert.Nil(t, err)
				assert.Contains(t, string(result), "{\"predictions\":[1,2]")
			},
		},
		{
			name: "Predict_RequestErr",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, httperrors.NewBadRequestError("error")).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				statusCode, result, err := inferenceCtrl.Predict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Equal(t, http.StatusBadRequest, statusCode)
				assert.Equal(t, "error", err.Error())
				assert.Nil(t, result)
			},
		},
		{
			name: "Predict_PredictErr",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				cacheMock.EXPECT().
					Get(c.Request.Context(), requestData).
					Return(200, []byte("cached"), false).
					Once()

				predictMock.EXPECT().
					One(c.Request.Context(), requestData).
					Return("", errors.New("error")).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				statusCode, result, err := inferenceCtrl.Predict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Equal(t, http.StatusInternalServerError, statusCode)
				assert.Equal(t, "error", err.Error())
				assert.Nil(t, result)
			},
		},
		{
			name: "Predict_PredictNotFoundErr",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				cacheMock.EXPECT().
					Get(c.Request.Context(), requestData).
					Return(200, []byte("cached"), false).
					Once()

				predictMock.EXPECT().
					One(c.Request.Context(), requestData).
					Return("", httperrors.NewNotFoundError("model not found")).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				statusCode, result, err := inferenceCtrl.Predict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Equal(t, http.StatusNotFound, statusCode)
				assert.Equal(t, "model not found", err.Error())
				assert.Nil(t, result)
			},
		},
		{
			name: "Explain_OK",
			setupMocks: func() {
				requestData.UseCache = entities.Never

				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				explainMock.EXPECT().
					One(c.Request.Context(), requestData).
					Return("{\"maps\":[1,2]}", nil).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.Explain(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, err)
				assert.Contains(t, string(result), "\"maps\":[1,2]")
			},
		},
		{
			name: "Explain_CacheNotSupported",
			setupMocks: func() {
				requestData.UseCache = entities.Always

				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				explainMock.EXPECT().
					One(c.Request.Context(), requestData).
					Return("predictions", nil).
					Maybe()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.Explain(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, result)
				assert.Equal(t, http.StatusBadRequest, err.StatusCode)
				assert.Equal(t, "Invalid parameter: `use_cache=always` is not supported for the `explain` endpoint.", err.Error())
			},
		},
		{
			name: "Explain_ExplainErr",
			setupMocks: func() {
				requestData.UseCache = entities.Never

				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				explainMock.EXPECT().
					One(c.Request.Context(), requestData).
					Return("", errors.New("error")).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.Explain(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, result)
				assert.Equal(t, http.StatusInternalServerError, err.StatusCode)
				assert.Equal(t, "error", err.Error())
			},
		},
		{
			name: "Predict_ExplainNotFoundErr",
			setupMocks: func() {
				requestData.UseCache = entities.Never

				requestHandlerMock.EXPECT().
					NewPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				explainMock.EXPECT().
					One(c.Request.Context(), requestData).
					Return("", httperrors.NewNotFoundError("model not found")).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.Explain(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Equal(t, http.StatusNotFound, err.StatusCode)
				assert.Equal(t, "model not found", err.Error())
				assert.Nil(t, result)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.setupMocks()

			tt.actionAndAssert(t)

			modelAccessMock.ExpectedCalls = nil
			cacheMock.ExpectedCalls = nil
			requestHandlerMock.ExpectedCalls = nil
			predictMock.ExpectedCalls = nil
			explainMock.ExpectedCalls = nil
		})
	}
}

func TestInferenceController_InferBatch(t *testing.T) {
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/path", nil)

	modelAccessMock := mockservice.NewMockModelAccessService(t)
	cacheMock := mockservice.NewMockCacheService(t)
	predictMock := mockusecase.NewMockInfer[usecase.BatchPredictionJSON](t)
	explainMock := mockusecase.NewMockInfer[usecase.BatchExplainJSON](t)
	requestHandlerMock := mockcontrollers.NewMockRequestHandler(t)

	entityID := sdkentities.ID{ID: "active"}
	fullVideoID := sdkentities.GetFullVideoID(t)
	inferenceRequest := &entities.InferenceRequest{
		OrganizationID: fullVideoID.OrganizationID.String(),
		WorkspaceID:    fullVideoID.WorkspaceID.String(),
		ProjectID:      fullVideoID.ProjectID.String(),
	}
	requestData := &entities.BatchPredictionRequestData{
		OrganizationID: fullVideoID.OrganizationID,
		WorkspaceID:    fullVideoID.WorkspaceID,
		ProjectID:      fullVideoID.ProjectID,
		ModelID:        entityID,
		Roi:            entities.Roi{X: 0, Y: 0, Width: 100, Height: 100},
		FrameSkip:      1,
		StartFrame:     1,
		EndFrame:       5,
		LabelOnly:      true,
		MediaInfo:      &entities.MediaInfo{FrameIndex: 1, DatasetID: fullVideoID.DatasetID, VideoID: fullVideoID.VideoID},
	}

	inferenceCtrl := NewInferenceControllerImpl(modelAccessMock, cacheMock, requestHandlerMock, predictMock, explainMock)

	tests := []struct {
		name            string
		setupMocks      func()
		actionAndAssert func(t *testing.T)
	}{
		{
			name: "Predict_OK",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewBatchPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				predictMock.EXPECT().
					Batch(c.Request.Context(), requestData).
					Return(&usecase.BatchPredictionJSON{BatchPredictions: make([]json.RawMessage, 0)}, nil).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.BatchPredict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, err)
				assert.NotNil(t, result)
			},
		},
		{
			name: "Predict_RequestErr",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewBatchPredictionRequest(c, inferenceRequest, entityID).
					Return(nil, errors.New("error")).
					Once()

				predictMock.EXPECT().
					Batch(c.Request.Context(), requestData).
					Return(&usecase.BatchPredictionJSON{BatchPredictions: make([]json.RawMessage, 0)}, nil).
					Maybe()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.BatchPredict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, result)
				assert.Equal(t, http.StatusBadRequest, err.StatusCode)
				assert.Equal(t, "error", err.Error())

				predictMock.AssertNotCalled(t, "Batch", c.Request.Context(), requestData)
			},
		},
		{
			name: "Predict_BatchErr",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewBatchPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				predictMock.EXPECT().
					Batch(c.Request.Context(), requestData).
					Return(nil, errors.New("error")).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.BatchPredict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, result)
				assert.Equal(t, http.StatusInternalServerError, err.StatusCode)
				assert.Equal(t, "error", err.Error())
			},
		},
		{
			name: "Predict_BatchNotFoundErr",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewBatchPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				predictMock.EXPECT().
					Batch(c.Request.Context(), requestData).
					Return(nil, httperrors.NewNotFoundError("model not found")).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.BatchPredict(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, result)
				assert.Equal(t, http.StatusNotFound, err.StatusCode)
				assert.Equal(t, "model not found", err.Error())
			},
		},
		{
			name: "Explain_OK",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewBatchPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				explainMock.EXPECT().
					Batch(c.Request.Context(), requestData).
					Return(&usecase.BatchExplainJSON{BatchExplain: make([]json.RawMessage, 0)}, nil).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.BatchExplain(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, err)
				assert.NotNil(t, result)
			},
		},
		{
			name: "Explain_RequestErr",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewBatchPredictionRequest(c, inferenceRequest, entityID).
					Return(nil, errors.New("error")).
					Once()

				explainMock.EXPECT().
					Batch(c.Request.Context(), requestData).
					Return(&usecase.BatchExplainJSON{BatchExplain: make([]json.RawMessage, 0)}, nil).
					Maybe()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.BatchExplain(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, result)
				assert.Equal(t, http.StatusBadRequest, err.StatusCode)
				assert.Equal(t, "error", err.Error())

				explainMock.AssertNotCalled(t, "Batch", c.Request.Context(), requestData)
			},
		},
		{
			name: "Explain_BatchErr",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewBatchPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				explainMock.EXPECT().
					Batch(c.Request.Context(), requestData).
					Return(nil, errors.New("error")).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.BatchExplain(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, result)
				assert.Equal(t, http.StatusInternalServerError, err.StatusCode)
				assert.Equal(t, "error", err.Error())
			},
		},
		{
			name: "Explain_BatchNotFoundErr",
			setupMocks: func() {
				requestHandlerMock.EXPECT().
					NewBatchPredictionRequest(c, inferenceRequest, entityID).
					Return(requestData, nil).
					Once()

				explainMock.EXPECT().
					Batch(c.Request.Context(), requestData).
					Return(nil, httperrors.NewNotFoundError("model not found")).
					Once()
			},
			actionAndAssert: func(t *testing.T) {
				result, err := inferenceCtrl.BatchExplain(c, inferenceRequest, sdkentities.ID{ID: "active"})

				assert.Nil(t, result)
				assert.Equal(t, http.StatusNotFound, err.StatusCode)
				assert.Equal(t, "model not found", err.Error())
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.setupMocks()

			tt.actionAndAssert(t)

			modelAccessMock.ExpectedCalls = nil
			cacheMock.ExpectedCalls = nil
			requestHandlerMock.ExpectedCalls = nil
			predictMock.ExpectedCalls = nil
			predictMock.Calls = nil
			explainMock.ExpectedCalls = nil
			explainMock.Calls = nil
		})
	}
}

func TestInferenceController_IsModelReady(t *testing.T) {
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/path", nil)

	modelAccessMock := mockservice.NewMockModelAccessService(t)
	cacheMock := mockservice.NewMockCacheService(t)
	predictMock := mockusecase.NewMockInfer[usecase.BatchPredictionJSON](t)
	explainMock := mockusecase.NewMockInfer[usecase.BatchExplainJSON](t)
	requestHandlerMock := mockcontrollers.NewMockRequestHandler(t)

	inferenceCtrl := NewInferenceControllerImpl(modelAccessMock, cacheMock, requestHandlerMock, predictMock, explainMock)

	modelAccessMock.EXPECT().
		IsModelReady(c.Request.Context(), "dummy_id").
		Return(true).
		Once()

	inferenceCtrl.IsModelReady(c, "dummy_id")
}
