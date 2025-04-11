// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"context"
	"net/http"

	"google.golang.org/grpc/metadata"
)

// AddAuthHeadersToContext adds relevant authentication headers from an HTTP request to a gRPC context
func AddAuthHeadersToContext(ctx context.Context, r *http.Request) context.Context {
	md := metadata.New(nil)

	if authHeader := r.Header.Get("Authorization"); authHeader != "" {
		md.Set("authorization", authHeader)
	}

	if accessToken := r.Header.Get("x-auth-request-access-token"); accessToken != "" {
		md.Set("x-auth-request-access-token", accessToken)
	}

	return metadata.NewOutgoingContext(ctx, md)
}
