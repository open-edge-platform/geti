// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package config

import (
	"context"

	"geti.com/iai_core/logger"
	"github.com/caarlos0/env/v11"
)

type envsConfig struct {
	AsynchronousMediaPreprocessing bool `env:"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING" envDefault:"false"`
}

func AsynchronousMediaPreprocessing(ctx context.Context) bool {
	cfg := envsConfig{}
	if err := env.Parse(&cfg); err != nil {
		logger.TracingLog(ctx).Errorf("Failed to parse environment variables: %s", err)
		return false
	}
	return cfg.AsynchronousMediaPreprocessing
}
