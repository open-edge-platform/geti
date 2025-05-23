// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"context"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewVideo(t *testing.T) {
	path := "../test_data/test_mp4.mp4"
	video := NewVideo(context.Background(), path)
	assert.Equal(t, path, video.FilePath)
	assert.InEpsilon(t, float64(30), video.FPS, 0.0001)
}

func TestFullVideoID(t *testing.T) {
	fullVideoID := GetFullVideoID(t)

	videoPath := filepath.Join(
		"organizations",
		fullVideoID.OrganizationID.String(),
		"workspaces",
		fullVideoID.WorkspaceID.String(),
		"projects",
		fullVideoID.ProjectID.String(),
		"dataset_storages",
		fullVideoID.DatasetID.String(),
		fullVideoID.VideoID.String(),
	)

	assert.Equal(t, videoPath, fullVideoID.GetPath())
}

func TestParseFpsFraction(t *testing.T) {
	tests := []struct {
		given string
		want  float64
	}{
		{
			given: "30000/1001",
			want:  29.97,
		},
		{
			given: "25/1",
			want:  25.0,
		},
		{
			given: "30/1",
			want:  30.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.given, func(t *testing.T) {
			assert.InEpsilon(t, tt.want, parseFPSFraction(tt.given), 0.0001)
		})
	}
}
