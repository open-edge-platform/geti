// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package account_service_grpc

import (
	"context"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/types/known/timestamppb"
	"os"
	"time"
)

const timeoutSeconds int = 30

func InitializeClient(serviceAddressEnv string, defaultAddress string) (*grpc.ClientConn, error) {
	accSvcAddress := os.Getenv(serviceAddressEnv)
	if accSvcAddress == "" {
		accSvcAddress = defaultAddress
	}
	ctx, _ := context.WithTimeout(context.Background(), time.Duration(timeoutSeconds)*time.Second)
	conn, err := grpc.DialContext(
		ctx,
		accSvcAddress,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
		grpc.WithDefaultServiceConfig(`{"loadBalancingPolicy":"round_robin"}`),
	)
	if err != nil {
		return nil, err
	}
	return conn, nil
}

func CloseClientConnection(conn *grpc.ClientConn) error {
	if conn == nil {
		return nil
	}
	return conn.Close()
}

func TimestampProtoToTime(ts *timestamppb.Timestamp) time.Time {
	if ts == nil {
		return time.Time{}
	}
	return ts.AsTime()
}

func TimeToTimestampProto(t time.Time) *timestamppb.Timestamp {
	return timestamppb.New(t)
}
