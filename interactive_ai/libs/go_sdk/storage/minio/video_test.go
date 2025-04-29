// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//go:build integration

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
