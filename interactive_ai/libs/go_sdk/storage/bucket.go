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

package storage

import (
	"fmt"
	"os"
	"strings"
)

const bucketNamePrefix = "BUCKET_NAME_"

// GetBucketName returns the bucket name based on the given object type.
// It retrieves the bucket name from the corresponding environment variable.
// If the environment variable is not set, it returns an error.
func GetBucketName(objectType string) (string, error) {
	bucketNameEnvVariable := bucketNamePrefix + strings.ToUpper(strings.ReplaceAll(objectType, "_", ""))
	bucketName := os.Getenv(bucketNameEnvVariable)
	if bucketName == "" {
		return "", fmt.Errorf("environment variable %s was not set, but this is needed for S3 to work",
			bucketNameEnvVariable)
	}
	return bucketName, nil
}
