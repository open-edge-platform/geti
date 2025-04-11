// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
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
	"context"

	"inference_gateway/app/entities"

	"geti.com/go_sdk/logger"
	"github.com/caarlos0/env/v11"
	"github.com/go-resty/resty/v2"
)

type CacheService interface {
	Get(ctx context.Context, request *entities.PredictionRequestData) (int, []byte, bool)
}

type directorConfig struct {
	Service string `env:"DIRECTOR_MS_SERVICE" envDefault:"impt-director"`
	Port    int    `env:"DIRECTOR_MS_PORT" envDefault:"4999"`
	Address string `env:"DIRECTOR_MS_ADDRESS,expand" envDefault:"http://$DIRECTOR_MS_SERVICE.impt:${DIRECTOR_MS_PORT}"`
}

type PredictionCacheService struct {
	client *resty.Client
}

func NewPredictionCacheService(client *resty.Client) (*PredictionCacheService, error) {
	cfg := directorConfig{}
	if err := env.Parse(&cfg); err != nil {
		return nil, err
	}
	return &PredictionCacheService{
		client: client.SetBaseURL(cfg.Address),
	}, nil
}

// Get checks if cache is available. If available, the endpoint path is returned at which the cache
// can be retrieved.
func (s *PredictionCacheService) Get(ctx context.Context, request *entities.PredictionRequestData) (int, []byte, bool) {
	// Cache is skipped when useCache equals never or an ROI is passed in the request.
	if request.UseCache == entities.Never || !request.Roi.IsNull() {
		return 0, nil, false
	}
	predictionURL := request.GetURL()
	logger.TracingLog(ctx).Infof("Fetching cached predictions via %s", predictionURL)

	resp, err := s.client.R().
		SetContext(ctx).
		Get(predictionURL)

	if err != nil {
		logger.TracingLog(ctx).Errorf("Error fetching cached predictions via %s: %s", predictionURL, err)
		return 0, nil, false
	}

	statusCode := resp.StatusCode()
	if statusCode == 200 || statusCode == 204 && request.UseCache == entities.Always {
		return statusCode, resp.Body(), true
	}

	// Failed to get a cached prediction
	return 0, nil, false
}
