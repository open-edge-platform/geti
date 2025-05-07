// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package service

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"time"

	"geti.com/iai_core/logger"
	"geti.com/iai_core/telemetry"
	pb "geti.com/predict"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"inference_gateway/app/entities"
	"inference_gateway/app/grpc"
)

const (
	InferTimeoutSeconds                          = 80
	ModelRecoveryStatusCheckIntervalMilliSeconds = 100
	ModelReadyRetries                            = 100
)

var (
	ErrModelNotFound     = errors.New("could not find a model for the inference request")
	ErrMediaNotSupported = errors.New("unable to process media of the provided type")
)

type InferParameters struct {
	imageReader     *bytes.Reader
	pipelineName    string
	includeXAI      bool
	roi             entities.Roi
	labelOnly       bool
	hyperParameters *string
}

// GetByteData returns the byte array containing the media data
func (ip *InferParameters) GetByteData() ([]byte, error) {
	if _, err := ip.imageReader.Seek(0, 0); err != nil {
		return nil, fmt.Errorf("failed to seek image: %w", err)
	}
	mediaBytes, err := io.ReadAll(ip.imageReader)
	if err != nil {
		return nil, fmt.Errorf("no media could be decoded from the request: %w", err)
	}
	if len(mediaBytes) == 0 {
		return nil, errors.New("no media could be decoded from the request")
	}
	return mediaBytes, nil
}

// NewInferParameters initializes the InferParameters
func NewInferParameters(buf *bytes.Buffer, pipelineName string, includeXAI bool, roi entities.Roi, labelOnly bool, hyperParameters *string) *InferParameters {
	return &InferParameters{
		imageReader:     bytes.NewReader(buf.Bytes()),
		pipelineName:    pipelineName,
		includeXAI:      includeXAI,
		roi:             roi,
		labelOnly:       labelOnly,
		hyperParameters: hyperParameters,
	}
}

type ModelAccessService interface {
	InferImageBytes(ctx context.Context, params InferParameters) (*pb.ModelInferResponse, error)
	TryRecoverModel(ctx context.Context, params InferParameters) (*pb.ModelInferResponse, error)
	IsModelReady(ctx context.Context, modelID string) bool
}

type ModelAccessServiceImpl struct {
	meshClient         *grpc.ModelMeshClient
	registrationClient *grpc.ModelMeshRegistrationClient
}

func NewModelAccessService(meshClient *grpc.ModelMeshClient, registrationClient *grpc.ModelMeshRegistrationClient) *ModelAccessServiceImpl {
	return &ModelAccessServiceImpl{
		meshClient:         meshClient,
		registrationClient: registrationClient,
	}
}

// InferImageBytes sends an inference request to a model in ModelMesh and returns the response.
func (s *ModelAccessServiceImpl) InferImageBytes(ctx context.Context, params InferParameters) (*pb.ModelInferResponse, error) {
	ctx, span := telemetry.Tracer().Start(ctx, "infer-image-bytes")
	defer span.End()

	request, err := createModelInferRequest(ctx, params)
	if err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(ctx, time.Duration(InferTimeoutSeconds)*time.Second)
	defer cancel()
	response, e := s.meshClient.ModelInfer(ctx, request)

	if e != nil {
		logger.TracingLog(ctx).Infof("grpc error encountered: %v", e)
		switch status.Code(e) {
		case codes.NotFound:
			return nil, ErrModelNotFound
		case codes.InvalidArgument:
			return nil, ErrMediaNotSupported
		default:
			return nil, fmt.Errorf("failed model infer request: %w", e)
		}
	}

	return response, nil
}

// TryRecoverModel Checks for a model not found error and retries initializing the model through model registration
func (s *ModelAccessServiceImpl) TryRecoverModel(ctx context.Context, params InferParameters) (*pb.ModelInferResponse, error) {
	ctx, span := telemetry.Tracer().Start(ctx, "try-recover-model")
	defer span.End()

	if recovered := s.registrationClient.RecoverModel(ctx, params.pipelineName); recovered {
		logger.TracingLog(ctx).Info("Model recovered successfully, awaiting model readiness")
		for retries := 0; retries < ModelReadyRetries; retries++ {
			if modelOk := s.meshClient.GetModelReady(ctx, params.pipelineName); modelOk {
				return s.InferImageBytes(ctx, params)
			}
			time.Sleep(time.Duration(ModelRecoveryStatusCheckIntervalMilliSeconds) * time.Millisecond)
		}
	}

	return nil, ErrModelNotFound
}

func (s *ModelAccessServiceImpl) IsModelReady(ctx context.Context, modelID string) bool {
	return s.meshClient.GetModelReady(ctx, modelID)
}

func createModelInferRequest(ctx context.Context, params InferParameters) (*pb.ModelInferRequest, error) {
	// Prepare infer request
	var request pb.ModelInferRequest

	// Setup shape
	inputTensor := &pb.ModelInferRequest_InferInputTensor{
		Name:     "input",
		Datatype: "UINT8",
		Shape:    []int64{-1, -1, -1, -1},
	}
	request.Inputs = append(request.Inputs, inputTensor)

	// Get byte data
	byteData, err := params.GetByteData()
	if err != nil {
		logger.TracingLog(ctx).Errorf("Error reading media byte data: %s", err)
		return nil, err
	}

	request.ModelName = params.pipelineName
	request.RawInputContents = [][]byte{byteData} // Byte data
	request.Parameters = createParameters(params) // Parameters

	return &request, nil
}

func createParameters(params InferParameters) map[string]*pb.InferParameter {
	parameters := setInferParameters(params)

	// Set ROI parameters
	if !params.roi.IsNull() {
		roiParameters := getRoiParameters(params.roi)
		// Append ROI parameters to existing parameters
		for k, v := range roiParameters {
			parameters[k] = v
		}
	}

	if params.hyperParameters != nil {
		parameters["hyper_parameters"] = &pb.InferParameter{
			ParameterChoice: &pb.InferParameter_StringParam{
				StringParam: *params.hyperParameters,
			},
		}
	}

	return parameters
}

func setInferParameters(params InferParameters) map[string]*pb.InferParameter {
	xaiParam := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_BoolParam{BoolParam: params.includeXAI},
	}
	labelOnly := pb.InferParameter{
		ParameterChoice: &pb.InferParameter_BoolParam{BoolParam: params.labelOnly},
	}

	return map[string]*pb.InferParameter{
		"include_xai": &xaiParam,
		"label_only":  &labelOnly,
	}
}

func getRoiParameters(roi entities.Roi) map[string]*pb.InferParameter {
	return map[string]*pb.InferParameter{
		"x":      {ParameterChoice: &pb.InferParameter_Int64Param{Int64Param: int64(roi.X)}},
		"y":      {ParameterChoice: &pb.InferParameter_Int64Param{Int64Param: int64(roi.Y)}},
		"width":  {ParameterChoice: &pb.InferParameter_Int64Param{Int64Param: int64(roi.Width)}},
		"height": {ParameterChoice: &pb.InferParameter_Int64Param{Int64Param: int64(roi.Height)}},
	}
}
