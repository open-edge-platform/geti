// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package grpc_gateway

import (
	"context"
	"net/http"
	"strconv"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"google.golang.org/grpc"
	"google.golang.org/grpc/metadata"
	"google.golang.org/protobuf/proto"

	"common/utils"
)

const HttpStatusCodeResponseHeader = "x-http-code"
const HttpStatusCodeForwardedResponseHeader = "Grpc-Metadata-X-Http-Code"

var logger = utils.InitializeLogger()

func SetCustomHTTPResponseStatusCode(ctx context.Context, statusCode int) {
	strStatusCode := strconv.Itoa(statusCode)
	err := grpc.SetHeader(ctx, metadata.Pairs(HttpStatusCodeResponseHeader, strStatusCode))
	if err != nil {
		logger.Errorf("error during setting custom HTTP response status: %v", err)
	}
}

func HTTPResponseModifier(ctx context.Context, w http.ResponseWriter, _ proto.Message) error {
	md, ok := runtime.ServerMetadataFromContext(ctx)
	if !ok {
		return nil
	}

	// set http status code
	if vals := md.HeaderMD.Get(HttpStatusCodeResponseHeader); len(vals) > 0 {
		code, err := strconv.Atoi(vals[0])
		if err != nil {
			return err
		}
		// delete the headers to not expose any grpc-metadata in http response
		delete(md.HeaderMD, HttpStatusCodeResponseHeader)
		delete(w.Header(), HttpStatusCodeForwardedResponseHeader)
		w.WriteHeader(code)
	}

	return nil
}

func HTTPRequestHeadersMatcher(key string) (string, bool) {
	switch key {
	case "X-Auth-Request-Access-Token":
		return key, true
	default:
		return key, false
	}
}
