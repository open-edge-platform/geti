// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
