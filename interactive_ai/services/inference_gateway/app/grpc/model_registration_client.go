// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package grpc

import (
	"context"
	"fmt"
	"time"

	"geti.com/iai_core/logger"
	"geti.com/iai_core/telemetry"
	mrpb "geti.com/modelregistration"
	"github.com/caarlos0/env/v11"
	"google.golang.org/grpc"
)

const RecoverModelTimeoutSeconds = 20

type modelRegistrationConfig struct {
	Service string `env:"MODELREGISTRATION_SERVICE"        envDefault:"impt-modelregistration"`
	Port    int    `env:"MODELREGISTRATION_PORT"           envDefault:"5555"`
	Address string `env:"MODELREGISTRATION_ADDRESS,expand" envDefault:"passthrough:///$MODELREGISTRATION_SERVICE.impt:${MODELREGISTRATION_PORT}"`
}

type ModelMeshRegistrationClient struct {
	mrpb.ModelRegistrationClient

	conn *grpc.ClientConn
}

// NewModelMeshRegistrationClient creates a new ModelMeshRegistrationClient.
func NewModelMeshRegistrationClient() (*ModelMeshRegistrationClient, error) {
	cfg := modelRegistrationConfig{}
	if err := env.Parse(&cfg); err != nil {
		return nil, err
	}

	logger.Log().Infof("Creating a new gRPC 'channel' for the target URI: %s...", cfg.Address)
	conn, err := NewGRPCClient(cfg.Address)

	if err != nil {
		return nil, fmt.Errorf("cannot create a new grpc client for %s: %w", cfg.Address, err)
	}
	logger.Log().Info("ModelRegistration gRPC client successfully created.")
	return &ModelMeshRegistrationClient{
		ModelRegistrationClient: mrpb.NewModelRegistrationClient(conn),
		conn:                    conn,
	}, nil
}

// Close closes the connection to the gRPC server.
func (mrc *ModelMeshRegistrationClient) Close() error {
	if err := mrc.conn.Close(); err != nil {
		return fmt.Errorf("error upon closing ModelRegistrationMS gRPC connection: %w", err)
	}
	return nil
}

// RecoverModel Make an attempt to recover a model. Returns true if recovery was successful.
func (mrc *ModelMeshRegistrationClient) RecoverModel(ctx context.Context, modelID string) bool {
	ctx, span := telemetry.Tracer().Start(ctx, "recover-model")
	defer span.End()

	request := mrpb.RecoverRequest{Name: modelID}
	ctx, cancel := context.WithTimeout(ctx, time.Duration(RecoverModelTimeoutSeconds)*time.Second)
	defer cancel()

	response, err := mrc.RecoverPipeline(ctx, &request)
	if err != nil {
		logger.TracingLog(ctx).Infof(
			"Failed to recover model `%s`, request failed with error: `%s`",
			modelID, err,
		)
		return false
	}
	return response.GetSuccess()
}
