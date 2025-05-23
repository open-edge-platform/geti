// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package storage

import (
	"fmt"
	"os"
	"strings"
)

// GetBucketName returns the bucket name based on the given object type.
// It retrieves the bucket name from the corresponding environment variable.
// If the environment variable is not set, it returns an error.
func GetBucketName(objectType string) (string, error) {
	const bucketNamePrefix = "BUCKET_NAME_"
	bucketNameEnvVariable := bucketNamePrefix + strings.ToUpper(strings.ReplaceAll(objectType, "_", ""))
	bucketName := os.Getenv(bucketNameEnvVariable)
	if bucketName == "" {
		return "", fmt.Errorf("environment variable %s was not set, but this is needed for S3 to work",
			bucketNameEnvVariable)
	}
	return bucketName, nil
}
