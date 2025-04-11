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
	"regexp"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"geti.com/go_sdk/entities"
	"geti.com/go_sdk/testhelper"
)

func TestLoadVideo(t *testing.T) {

	// Since the repository implementation relies on a global variable, it isn't mocked out and
	// relies on the running test container for the underlying infrastructure or services.
	// Test container infra prepared in main_test.go.

	fullVideoID := entities.GetFullVideoID(t)
	ctx := context.Background()
	_, err := testhelper.PrepareTestVideo(ctx, fullVideoID,
		"../../test_data/test_mp4.mp4")
	require.NoError(t, err)

	videoRepo := NewVideoRepositoryImpl()
	v, err := videoRepo.LoadVideoByID(ctx, fullVideoID)

	assert.NoError(t, err)
	assert.Regexp(t, regexp.MustCompile(`http://localhost:(\d*)/.*`), v.FilePath)
	assert.Equal(t, float64(30), v.FPS)
}
