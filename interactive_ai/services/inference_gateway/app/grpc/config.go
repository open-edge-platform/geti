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

package grpc

import (
	"time"

	"github.com/grpc-ecosystem/go-grpc-middleware/v2/interceptors/retry"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"
)

const (
	retryBackoffDurationMs = 200
	maxRetryAttempts       = 5
)

var keepAlive = keepalive.ClientParameters{
	Time:                10 * time.Second,
	Timeout:             time.Second,
	PermitWithoutStream: true,
}

var retryOpts = []retry.CallOption{
	retry.WithMax(maxRetryAttempts),
	retry.WithBackoff(retry.BackoffExponential(retryBackoffDurationMs * time.Millisecond)),
	retry.WithCodes(codes.Unavailable, codes.DeadlineExceeded),
}

var serviceCfg = `{
	"methodConfig": [{
		"name": [{}],
		"timeout": "3s"
	}]
}`

func NewGRPCClient(address string) (*grpc.ClientConn, error) {
	return grpc.NewClient(
		address,
		grpc.WithUnaryInterceptor(retry.UnaryClientInterceptor(retryOpts...)),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithDefaultServiceConfig(serviceCfg),
		grpc.WithKeepaliveParams(keepAlive),
	)
}
