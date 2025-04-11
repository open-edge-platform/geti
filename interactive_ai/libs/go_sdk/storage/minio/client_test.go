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

package minio

import (
	"context"
	"testing"

	"github.com/minio/minio-go/v7"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMinio(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		name   string
		bucket string
		action func(*testing.T) (*minio.Client, error)
	}{
		{
			name:   "GetClient",
			bucket: "get-bucket",
			action: func(_ *testing.T) (*minio.Client, error) {
				return getMinioClient(ctx)
			},
		},
		{
			name:   "ResetClient",
			bucket: "reset-bucket",
			action: func(t *testing.T) (*minio.Client, error) {
				_, err := getMinioClient(ctx)
				require.NoError(t, err)
				reset()
				return getMinioClient(ctx)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			client, err := tt.action(t)
			require.NoError(t, err)
			err = client.MakeBucket(ctx, tt.bucket, minio.MakeBucketOptions{})
			require.NoError(t, err)
			exists, err := client.BucketExists(ctx, tt.bucket)
			require.NoError(t, err)

			assert.True(t, exists, "Bucket %s doesn't exist", tt.bucket)
		})
	}
}
