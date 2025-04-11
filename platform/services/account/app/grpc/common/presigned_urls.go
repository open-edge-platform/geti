// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package common

import (
	"context"
	"net/url"

	grpcUtils "account_service/app/grpc/utils"
	"account_service/app/storage"
)

func GetPresignedUrlWithMaybeReplacedHost(grpcContext context.Context,
	s3handle *storage.S3Storage, filename string) (presignedUrl string, err error) {

	presignedUrl, err = s3handle.GetPresignedUrl(filename)
	if err != nil {
		return presignedUrl, err
	}

	parsedPresignedURL, err := url.Parse(presignedUrl)
	if err != nil {
		logger.Errorf("failed to parse presigned URL, err: %v", err)
		return presignedUrl, err
	}

	hostHeaderValue, ok := grpcUtils.GetHTTPHeaderFromGRPCContext(grpcContext, "x-forwarded-host")
	if ok {
		parsedPresignedURL.Host = hostHeaderValue
	}

	parsedPresignedURL.Scheme = "https"
	parsedPresignedURL.Path = "/api/v1/fileservice" + parsedPresignedURL.Path

	return parsedPresignedURL.String(), nil
}
