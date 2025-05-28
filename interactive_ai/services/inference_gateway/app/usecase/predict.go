// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//nolint:dupl // Will be refactored in the future
package usecase

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"

	sdkentities "geti.com/iai_core/entities"
	"geti.com/iai_core/frames"
	"geti.com/iai_core/logger"
	"geti.com/iai_core/storage"
	"geti.com/iai_core/telemetry"
	"golang.org/x/sync/errgroup"

	"inference_gateway/app/entities"
	"inference_gateway/app/service"
)

type Predict struct {
	modelAccess    service.ModelAccessService
	videoRepo      storage.VideoRepository
	frameExtractor frames.CLIFrameExtractor
	semaCh         chan struct{}
}

func NewPredict(
	modelAccess service.ModelAccessService,
	videoRepo storage.VideoRepository,
	frameExtractor frames.CLIFrameExtractor,
) *Predict {
	return &Predict{
		modelAccess:    modelAccess,
		videoRepo:      videoRepo,
		frameExtractor: frameExtractor,
		semaCh:         make(chan struct{}, MaxConcurrentInferenceRequests),
	}
}

type BatchPredictionJSON struct {
	BatchPredictions []json.RawMessage `json:"batch_predictions"`
}

func (uc *Predict) One(ctx context.Context, request *entities.PredictionRequestData) (string, error) {
	modelName := request.ProjectID.String() + "-" + request.ModelID.String()

	inferParams := service.NewInferParameters(
		request.Media,
		modelName,
		false,
		request.Roi,
		request.LabelOnly,
		request.HyperParameters,
	)
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

func (uc *Predict) Batch(
	ctx context.Context,
	request *entities.BatchPredictionRequestData,
) (*BatchPredictionJSON, error) {
	fullVideoID := sdkentities.NewFullVideoID(request.OrganizationID.String(),
		request.WorkspaceID.String(), request.ProjectID.String(),
		request.MediaInfo.DatasetID.String(), request.MediaInfo.VideoID.String())
	video, err := uc.videoRepo.LoadVideoByID(ctx, fullVideoID)
	if err != nil {
		return nil, err
	}

	c, span := telemetry.Tracer().Start(ctx, "predict-loop")
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

			jsonData, reqErr := req.ToPredictBytes(result)
			if reqErr != nil {
				return fmt.Errorf("failed to construct JSON response from prediction string: %w", reqErr)
			}
			inferResults[frame.Index] = jsonData
			return nil
		})
	}

	err = <-doneCh
	if err != nil {
		telemetry.RecordError(span, err)
		return nil, fmt.Errorf("error during frame extraction process: %w", err)
	}
	if err = g.Wait(); err != nil {
		telemetry.RecordError(span, err)
		return nil, fmt.Errorf("error during one of the inference requests: %w", err)
	}

	var batchPredictionJSON BatchPredictionJSON
	batchPredictionJSON.BatchPredictions = make([]json.RawMessage, totalRequests)
	for i, result := range inferResults {
		batchPredictionJSON.BatchPredictions[i] = result
	}

	return &batchPredictionJSON, nil
}
