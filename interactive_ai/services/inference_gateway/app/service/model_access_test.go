// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package service

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"image/jpeg"
	"testing"

	mmpb "geti.com/modelmesh"
	modelmesh "geti.com/modelmesh/mock"
	mrpb "geti.com/modelregistration"
	modelregistration "geti.com/modelregistration/mock"
	pb "geti.com/predict"
	predictv2 "geti.com/predict/mock"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"inference_gateway/app/entities"
	"inference_gateway/app/grpc"
	testhelpers "inference_gateway/app/test_helpers"
)

func createInferParameters() *InferParameters {
	mockData := []byte("mock image data")
	mockBuffer := bytes.NewBuffer(mockData)
	roi := entities.Roi{X: 0, Y: 0, Width: 100, Height: 100}
	return NewInferParameters(mockBuffer, "mockPipeline", false, roi, false, nil)
}

func TestErrors(t *testing.T) {
	ctx := context.Background()

	meshMock := modelmesh.NewMockModelMeshClient(t)
	registrationMock := modelregistration.NewMockModelRegistrationClient(t)
	inferenceMock := predictv2.NewMockGRPCInferenceServiceClient(t)
	mmc := &grpc.ModelMeshClient{
		GRPCInferenceServiceClient: inferenceMock,
		ModelMeshClient:            meshMock,
	}
	reg := &grpc.ModelMeshRegistrationClient{
		ModelRegistrationClient: registrationMock,
	}
	modelAccessSrv := NewModelAccessService(mmc, reg)

	tests := []struct {
		name       string
		setupMocks func()
		wantErr    error
	}{
		{
			name: "Model not found error",
			setupMocks: func() {
				inferenceMock.EXPECT().
					ModelInfer(mock.Anything, mock.Anything).
					Return(nil, status.Error(codes.NotFound, "model not found"))
			},
			wantErr: ErrModelNotFound,
		},
		{
			name: "Media not supported error",
			setupMocks: func() {
				inferenceMock.EXPECT().
					ModelInfer(mock.Anything, mock.Anything).
					Return(nil, status.Error(codes.InvalidArgument, "invalid argument"))
			},
			wantErr: ErrMediaNotSupported,
		},
		{
			name: "Context deadline error",
			setupMocks: func() {
				inferenceMock.EXPECT().
					ModelInfer(mock.Anything, mock.Anything).
					Return(nil, status.Error(codes.DeadlineExceeded, "deadline exceeded"))
			},
			wantErr: fmt.Errorf("failed model infer request: deadline exceeded"),
		},
		{
			name: "Remote connection error",
			setupMocks: func() {
				inferenceMock.EXPECT().
					ModelInfer(mock.Anything, mock.Anything).
					Return(nil, status.Error(codes.Unavailable, "remote connection failure"))
			},
			wantErr: fmt.Errorf("failed model infer request: remote connection failure"),
		},
		{
			name: "General error",
			setupMocks: func() {
				inferenceMock.EXPECT().
					ModelInfer(mock.Anything, mock.Anything).
					Return(nil, errors.New("general error"))
			},
			wantErr: fmt.Errorf("failed model infer request: general error"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.setupMocks != nil {
				tt.setupMocks()
			}

			_, err := modelAccessSrv.InferImageBytes(ctx, *createInferParameters())

			assert.Error(t, err, tt.wantErr)

			inferenceMock.ExpectedCalls = nil
			inferenceMock.Calls = nil
		})
	}
}

func TestInferImageBytes(t *testing.T) {
	// Prepare InferImageBytes call parameters
	img := testhelpers.GetUniformTestImage(10, 10, uint8(155))
	imgBuf := new(bytes.Buffer)
	_ = jpeg.Encode(imgBuf, img, nil)
	pipelineName := "project_id-model_id"

	// Format expected request
	buf := new(bytes.Buffer)
	err := jpeg.Encode(buf, img, nil)
	assert.Nil(t, err)

	var pbRequest pb.ModelInferRequest
	pbRequest.ModelName = pipelineName
	pbRequest.RawInputContents = [][]byte{buf.Bytes()}

	inferInput := pb.ModelInferRequest_InferInputTensor{
		Name:     "input",
		Datatype: "UINT8",
		Shape:    []int64{-1, -1, -1, -1},
	}
	pbRequest.Inputs = []*pb.ModelInferRequest_InferInputTensor{&inferInput}

	xaiParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_BoolParam{BoolParam: true},
	}
	labelOnlyParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_BoolParam{BoolParam: false},
	}
	xParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_Int64Param{Int64Param: 0},
	}
	yParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_Int64Param{Int64Param: 0},
	}
	widthParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_Int64Param{Int64Param: 10},
	}
	heightParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_Int64Param{Int64Param: 10},
	}
	pbRequest.Parameters = map[string]*pb.InferParameter{
		"include_xai": &xaiParam,
		"label_only":  &labelOnlyParam,
		"x":           &xParam,
		"y":           &yParam,
		"width":       &widthParam,
		"height":      &heightParam,
	}

	// Format expected ModelMesh response
	var pbResponse pb.ModelInferResponse
	testMapData := "test_map"
	testPredictionsData := "test_predictions"
	mapsParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_StringParam{StringParam: testMapData},
	}
	predictionsParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_StringParam{StringParam: testPredictionsData},
	}
	pbResponse.Parameters = map[string]*pb.InferParameter{
		"maps":        &mapsParam,
		"predictions": &predictionsParam,
	}
	pbResponse.ModelName = pipelineName

	meshMock := modelmesh.NewMockModelMeshClient(t)
	registrationMock := modelregistration.NewMockModelRegistrationClient(t)
	inferenceMock := predictv2.NewMockGRPCInferenceServiceClient(t)
	mmc := &grpc.ModelMeshClient{
		GRPCInferenceServiceClient: inferenceMock,
		ModelMeshClient:            meshMock,
	}
	reg := &grpc.ModelMeshRegistrationClient{
		ModelRegistrationClient: registrationMock,
	}
	modelAccessSrv := NewModelAccessService(mmc, reg)
	inferenceMock.EXPECT().ModelInfer(mock.Anything, &pbRequest).Return(&pbResponse, nil)

	// Make the call to InferImage
	inferParams := NewInferParameters(buf, pipelineName, true, entities.Roi{Height: 10, Width: 10}, false, nil)
	response, err := modelAccessSrv.InferImageBytes(context.Background(), *inferParams)

	// Assert response is as expected
	assert.Nil(t, err)
	assert.Equal(t, testMapData, response.GetParameters()["maps"].GetStringParam())
	assert.Equal(t, testPredictionsData, response.GetParameters()["predictions"].GetStringParam())
	assert.Equal(t, pipelineName, response.GetModelName())
}

func TestInferParameters(t *testing.T) {
	img := testhelpers.GetUniformTestImage(10, 10, uint8(155))
	pipelineName := "project_id-model_id"
	buf := new(bytes.Buffer)
	err := jpeg.Encode(buf, img, nil)
	assert.Nil(t, err)

	ip := NewInferParameters(buf, pipelineName, true, entities.Roi{}, false, nil)

	// Assert that reading works once
	imageBytes, e := ip.GetByteData()
	assert.Nil(t, e)
	newBuf := new(bytes.Buffer)
	err = jpeg.Encode(newBuf, img, nil)
	assert.Nil(t, err)
	assert.Equal(t, newBuf.Bytes(), imageBytes)

	// Assert that reading works the second time as well
	imageBytes2, e2 := ip.GetByteData()
	assert.Nil(t, e2)
	assert.NotNil(t, imageBytes2)
	assert.Equal(t, newBuf.Bytes(), imageBytes2)
}

func TestInferHyperParameters(t *testing.T) {
	img := testhelpers.GetUniformTestImage(10, 10, uint8(155))
	pipelineName := "project_id-model_id"
	buf := new(bytes.Buffer)
	err := jpeg.Encode(buf, img, nil)
	assert.Nil(t, err)
	hp := "{'task_id':1, 'confidence_treshold':0.35}"

	ip := NewInferParameters(buf, pipelineName, true, entities.Roi{}, false, &hp)

	imageBytes, e := ip.GetByteData()
	assert.Nil(t, e)
	newBuf := new(bytes.Buffer)
	err = jpeg.Encode(newBuf, img, nil)
	assert.Nil(t, err)
	assert.Equal(t, newBuf.Bytes(), imageBytes)
	assert.Equal(t, ip.hyperParameters, &hp)
}

// Test happy flow for inference error handling. For the test to pass, we:
// 1. Pass 'Model not found error' and inference parameters to error handler function
// 2. Expect a RecoverModel call to model registration microservice -> mock Success response
// 3. Expect a 'Get Model status' call to ModelMesh -> mock ModelReady response
// 4. Expect a 'ModelInfer' call to ModelMesh runtime -> mock predictions response
func TestHandleModelNotFoundError(t *testing.T) {

	// Prepare InferImage call parameters
	img := testhelpers.GetUniformTestImage(10, 10, uint8(155))
	pipelineName := "project_id-model_id"

	// Mock the model mesh and model registration client
	meshMock := modelmesh.NewMockModelMeshClient(t)
	registrationMock := modelregistration.NewMockModelRegistrationClient(t)
	inferenceMock := predictv2.NewMockGRPCInferenceServiceClient(t)
	mmc := &grpc.ModelMeshClient{
		GRPCInferenceServiceClient: inferenceMock,
		ModelMeshClient:            meshMock,
	}
	reg := &grpc.ModelMeshRegistrationClient{
		ModelRegistrationClient: registrationMock,
	}
	modelAccessSrv := NewModelAccessService(mmc, reg)

	// Create media buffer
	buf := new(bytes.Buffer)
	err := jpeg.Encode(buf, img, nil)
	assert.Nil(t, err)

	inferParams := NewInferParameters(buf, pipelineName, false, entities.Roi{}, false, nil)

	// Format expected recover request and mocked response
	request := mrpb.RecoverRequest{Name: pipelineName}
	response := mrpb.RecoverResponse{Success: true}
	registrationMock.EXPECT().RecoverPipeline(mock.Anything, &request).Return(&response, nil)

	// Format expected model status request and mocked response
	statusRequest := mmpb.GetVModelStatusRequest{VModelId: pipelineName}
	const status mmpb.VModelStatusInfo_VModelStatus = 1
	const activeStatus mmpb.ModelStatusInfo_ModelStatus = 3
	statusResponse := mmpb.VModelStatusInfo{
		Status:            status,
		ActiveModelStatus: &mmpb.ModelStatusInfo{Status: activeStatus},
		ActiveModelId:     pipelineName,
		TargetModelId:     pipelineName,
	}
	meshMock.EXPECT().GetVModelStatus(mock.Anything, &statusRequest).Return(&statusResponse, nil)

	// Format expected model Infer request and mocked response
	var pbRequest pb.ModelInferRequest
	pbRequest.ModelName = pipelineName
	pbRequest.RawInputContents = [][]byte{buf.Bytes()}
	inferInput := pb.ModelInferRequest_InferInputTensor{
		Name:     "input",
		Datatype: "UINT8",
		Shape:    []int64{-1, -1, -1, -1},
	}
	pbRequest.Inputs = []*pb.ModelInferRequest_InferInputTensor{&inferInput}
	xaiParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_BoolParam{BoolParam: false},
	}
	labelOnlyParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_BoolParam{BoolParam: false},
	}
	pbRequest.Parameters = map[string]*pb.InferParameter{
		"include_xai": &xaiParam,
		"label_only":  &labelOnlyParam,
	}
	var pbResponse pb.ModelInferResponse
	testPredictionsData := "test_predictions"
	predictionsParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_StringParam{StringParam: testPredictionsData},
	}
	pbResponse.Parameters = map[string]*pb.InferParameter{
		"predictions": &predictionsParam,
	}
	pbResponse.ModelName = pipelineName
	inferenceMock.EXPECT().ModelInfer(mock.Anything, &pbRequest).Return(&pbResponse, nil)

	// Act
	inferResponse, inferErr := modelAccessSrv.TryRecoverModel(context.Background(), *inferParams)

	// Assert no errors arise and predictions are returned
	assert.Nil(t, inferErr)
	assert.Equal(t, testPredictionsData, inferResponse.GetParameters()["predictions"].GetStringParam())
}
