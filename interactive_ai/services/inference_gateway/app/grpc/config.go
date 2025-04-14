// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
