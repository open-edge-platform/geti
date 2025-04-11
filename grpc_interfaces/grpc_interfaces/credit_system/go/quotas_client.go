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

package credit_system

import (
	"context"
	"fmt"
	"os"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "geti.com/credit_system/pb"
)

type QuotaType string

const (
	MaxUsersCount   QuotaType = "MAX_USERS_COUNT"
	MaxTrainingJobs QuotaType = "MAX_TRAINING_JOBS"
)

const timeoutSeconds int = 30

type QuotasClient struct {
	client     pb.QuotaServiceClient
	connection *grpc.ClientConn
}

func InitializeQuotasClient() (QuotasClient, error) {
	creditSystemAddress := os.Getenv("CREDITS_SERVICE")
	if creditSystemAddress == "" {
		creditSystemAddress = "credit-system.impt:5556"
	}
	// Set up gRPC connection, timeout after 30 secs
	ctx, _ := context.WithTimeout(context.Background(), time.Duration(timeoutSeconds)*time.Second)
	conn, err := grpc.DialContext(
		ctx,
		creditSystemAddress,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
		grpc.WithDefaultServiceConfig(`{"loadBalancingPolicy":"round_robin"}`),
	)

	if err != nil {
		return QuotasClient{}, err
	}
	qc := QuotasClient{
		client:     pb.NewQuotaServiceClient(conn),
		connection: conn,
	}
	return qc, nil
}

func (qc *QuotasClient) IsInitialized() bool {
	return qc.client != nil && qc.connection != nil
}

func (qc *QuotasClient) CloseConnection() bool {
	if !qc.IsInitialized() {
		return false
	}
	err := qc.connection.Close()
	if err != nil {
		return false
	}
	qc.client = nil
	qc.connection = nil
	return true
}

func (qc *QuotasClient) getQuotaByType(ctx context.Context, organizationId string, quotaType string) (*pb.QuotaInfo, error) {
	request := &pb.QuotaGetRequest{OrganizationId: organizationId, QuotaType: quotaType}

	// Configure context with timeout
	ctx, cancel := context.WithTimeout(ctx, time.Duration(timeoutSeconds)*time.Second)
	defer cancel()

	response, err := qc.client.Get(ctx, request)
	if err != nil {
		return nil, err
	}
	businessErr := response.GetError()
	if businessErr != nil {
		return nil, fmt.Errorf(businessErr.Message)
	}
	return response.GetQuotaInfo(), nil
}

func (qc *QuotasClient) GetUsersQuota(ctx context.Context, organizationId string) (*pb.QuotaInfo, error) {
	return qc.getQuotaByType(ctx, organizationId, string(MaxUsersCount))
}

func (qc *QuotasClient) GetJobsQuota(ctx context.Context, organizationId string) (*pb.QuotaInfo, error) {
	return qc.getQuotaByType(ctx, organizationId, string(MaxTrainingJobs))
}
