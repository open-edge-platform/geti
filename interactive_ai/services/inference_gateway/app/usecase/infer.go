// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package usecase

import (
	"context"

	"inference_gateway/app/entities"
)

const MaxConcurrentInferenceRequests = 100

type Infer[T BatchPredictionJSON | BatchExplainJSON] interface {
	One(ctx context.Context, request *entities.PredictionRequestData) (string, error)
	Batch(ctx context.Context, request *entities.BatchPredictionRequestData) (*T, error)
}
