// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
	assert.Equal(t, float64(30), video.FPS)
}

func TestFullVideoID(t *testing.T) {
	fullVideoID := GetFullVideoID(t)

	videoPath := filepath.Join("organizations", fullVideoID.OrganizationID.String(), "workspaces", fullVideoID.WorkspaceID.String(), "projects",
		fullVideoID.ProjectID.String(), "dataset_storages", fullVideoID.DatasetID.String(), fullVideoID.VideoID.String())

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
			assert.Equal(t, tt.want, parseFPSFraction(tt.given))
		})
	}
}
