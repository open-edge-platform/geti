// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package storage

import (
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGetBucketName(t *testing.T) {
	const bucketEnvVarName = "BUCKET_NAME_IMG"
	tests := []struct {
		give     string
		giveType string
		setupEnv func()
		want     string
	}{
		{
			give:     "EnvVarExists",
			giveType: "imgType",
			setupEnv: func() { _ = os.Setenv(bucketEnvVarName, "test") },
			want:     "test",
		},
		{
			give:     "NoEnvVarExists",
			giveType: "imgType",
			setupEnv: func() { _ = os.Unsetenv(bucketEnvVarName) },
			want:     "test",
		},
	}

	for _, tt := range tests {
		t.Run(tt.give, func(t *testing.T) {
			if tt.setupEnv != nil {
				tt.setupEnv()
			}
			bucketName, err := GetBucketName(tt.giveType)
			if err != nil {
				assert.Empty(t, bucketName, "Bucket name should be empty")
				assert.ErrorContains(t, err, "environment variable BUCKET_NAME_IMGTYPE was not set, but this is needed for S3 to work")
				return
			}
			assert.Nil(t, err)
			assert.Equal(t, tt.want, bucketName, "Bucket name doesn't match the expected value")
		})
	}
}
