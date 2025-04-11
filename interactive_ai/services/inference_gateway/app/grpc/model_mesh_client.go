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

package grpc

import (
	"context"
	"fmt"
	"time"

	"geti.com/go_sdk/logger"
	"geti.com/go_sdk/telemetry"
	"github.com/caarlos0/env/v11"
	"google.golang.org/grpc"
	"google.golang.org/grpc/status"

	mmpb "geti.com/modelmesh"
	pb "geti.com/predict"
)

const ModelStatusTimeoutSeconds = 20

type modelMeshConfig struct {
	Service string `env:"MODELMESH_SERVICE" envDefault:"modelmesh-serving.impt"`
	Port    int    `env:"MODELMESH_PORT" envDefault:"8033"`
	Address string `env:"MODELMESH_ADDRESS,expand" envDefault:"passthrough:///$MODELMESH_SERVICE:${MODELMESH_PORT}"`
}

// ModelMeshClient This type holds the gRPC connection and the clients for model mesh communication.
// The InferClient can make ModelInfer requests, while the mmClient can query model status.
type ModelMeshClient struct {
	pb.GRPCInferenceServiceClient
	mmpb.ModelMeshClient

	conn *grpc.ClientConn
}

// NewModelMeshClient Create a new ModelMeshClient instance with exponential backoff retry policy.
func NewModelMeshClient() (*ModelMeshClient, error) {
	cfg := modelMeshConfig{}
	if err := env.Parse(&cfg); err != nil {
		return nil, err
	}

	logger.Log().Infof("Creating a new gRPC 'channel' for the target URI: %s...", cfg.Address)
	conn, err := NewGRPCClient(cfg.Address)

	if err != nil {
		return nil, fmt.Errorf("cannot create a new grpc client for %s: %w", cfg.Address, err)
	}
	logger.Log().Info("ModelMesh gRPC client successfully created.")
	return &ModelMeshClient{
		GRPCInferenceServiceClient: pb.NewGRPCInferenceServiceClient(conn),
		ModelMeshClient:            mmpb.NewModelMeshClient(conn),
		conn:                       conn,
	}, nil
}

// Close closes the connection to the gRPC server.
func (mmc *ModelMeshClient) Close() error {
	logger.Log().Info("Closing ModelMesh connection.")
	if err := mmc.conn.Close(); err != nil {
		return fmt.Errorf("error upon closing ModelMesh gRPC connection: %w", err)
	}
	return nil
}

// GetModelReady Get the model readiness status for a specific model.
func (mmc *ModelMeshClient) GetModelReady(ctx context.Context, modelID string) bool {
	ctx, span := telemetry.Tracer().Start(ctx, "get-model-ready")
	defer span.End()

	request := mmpb.GetVModelStatusRequest{VModelId: modelID}
	ctx, cancel := context.WithTimeout(ctx, time.Duration(ModelStatusTimeoutSeconds)*time.Second)
	defer cancel()

	response, err := mmc.GetVModelStatus(ctx, &request)
	if err != nil {
		logger.TracingLog(ctx).Infof(
			"Failed to get status for model `%s`, request failed with gRPC status code: `%s`",
			modelID, status.Code(err).String(),
		)
		return false
	}

	getStatus := response.GetStatus()
	activeStatus := response.GetActiveModelStatus().GetStatus()
	logger.TracingLog(ctx).Infof("Received status=%s, active status=%s", getStatus, activeStatus)
	return getStatus == 1 && activeStatus == 3
}
