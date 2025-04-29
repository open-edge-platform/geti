// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package usecase

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"

	sdkentities "geti.com/go_sdk/entities"
	"geti.com/go_sdk/frames"
	"geti.com/go_sdk/logger"
	"geti.com/go_sdk/storage"
	"geti.com/go_sdk/telemetry"
	"golang.org/x/sync/errgroup"

	"inference_gateway/app/entities"
	"inference_gateway/app/service"
)

type Explain struct {
	modelAccess    service.ModelAccessService
	videoRepo      storage.VideoRepository
	frameExtractor frames.CLIFrameExtractor
	semaCh         chan struct{}
}

func NewExplain(modelAccess service.ModelAccessService, videoRepo storage.VideoRepository, frameExtractor frames.CLIFrameExtractor) *Explain {
	return &Explain{
		modelAccess:    modelAccess,
		videoRepo:      videoRepo,
		frameExtractor: frameExtractor,
		semaCh:         make(chan struct{}, MaxConcurrentInferenceRequests),
	}
}

type BatchExplainJSON struct {
	BatchExplain []json.RawMessage `json:"explanations"`
}

func (uc *Explain) One(ctx context.Context, request *entities.PredictionRequestData) (string, error) {
	modelName := request.ProjectID.String() + "-" + request.ModelID.String()

	inferParams := service.NewInferParameters(request.Media, modelName, true, request.Roi, request.LabelOnly, request.HyperParameters)
	response, err := uc.modelAccess.InferImageBytes(ctx, *inferParams)
	if errors.Is(err, service.ErrModelNotFound) {
		logger.TracingLog(ctx).Infof("`Model not found` error encountered, attempting to recover model `%s`", modelName)
		response, err = uc.modelAccess.TryRecoverModel(ctx, *inferParams)
		if err != nil {
			return "", err
		}
	} else if err != nil {
		return "", err
	}
	return response.GetParameters()["predictions"].GetStringParam(), nil
}

func (uc *Explain) Batch(ctx context.Context, request *entities.BatchPredictionRequestData) (*BatchExplainJSON, error) {
	fullVideoID := sdkentities.NewFullVideoID(request.OrganizationID.String(),
		request.WorkspaceID.String(), request.ProjectID.String(),
		request.MediaInfo.DatasetID.String(), request.MediaInfo.VideoID.String())
	video, err := uc.videoRepo.LoadVideoByID(ctx, fullVideoID)
	if err != nil {
		return nil, err
	}

	c, span := telemetry.Tracer().Start(ctx, "explain-loop")
	defer span.End()
	totalRequests := (request.EndFrame-request.StartFrame)/request.FrameSkip + 1
	inferResults := make([][]byte, totalRequests)
	pr, pw := io.Pipe()
	doneCh := uc.frameExtractor.Start(c, video, request.StartFrame, request.EndFrame, request.FrameSkip, pw)
	g, gCtx := errgroup.WithContext(c)

	for frame := range uc.frameExtractor.Read(c, pr) {
		g.Go(func() error {
			select {
			case uc.semaCh <- struct{}{}:
				defer func() { <-uc.semaCh }()
			case <-gCtx.Done():
				return gCtx.Err()
			}

			req := request.ToSingleRequest()
			req.MediaInfo.FrameIndex = request.StartFrame + frame.Index*request.FrameSkip
			req.Media = bytes.NewBuffer(frame.Data)
			result, inferErr := uc.One(gCtx, req)
			if inferErr != nil {
				return inferErr
			}

			jsonData, err := req.ToExplainBytes(result)
			if err != nil {
				return fmt.Errorf("failed to construct JSON response from prediction string: %w", err)
			}
			inferResults[frame.Index] = jsonData
			return nil
		})
	}

	err = <-doneCh
	if err != nil {
		telemetry.RecordError(span, err)
		return nil, fmt.Errorf("error during frame extraction process: %s", err)
	}
	if err := g.Wait(); err != nil {
		telemetry.RecordError(span, err)
		return nil, fmt.Errorf("error during one of the inference requests: %s", err)
	}

	var batchExplainJSON BatchExplainJSON
	batchExplainJSON.BatchExplain = make([]json.RawMessage, totalRequests)
	for i, result := range inferResults {
		batchExplainJSON.BatchExplain[i] = result
	}

	return &batchExplainJSON, nil
}
