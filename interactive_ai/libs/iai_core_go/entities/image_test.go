// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestFullImageID(t *testing.T) {
	fullImageID := GetFullImageID(t)

	tests := []struct {
		name   string
		action func() string
		want   string
	}{
		{
			name: "GetImagePath",
			action: func() string {
				return fullImageID.GetPath()
			},
			want: filepath.Join("organizations", fullImageID.OrganizationID.String(), "workspaces", fullImageID.WorkspaceID.String(), "projects",
				fullImageID.ProjectID.String(), "dataset_storages", fullImageID.DatasetID.String(), fullImageID.ImageID.String()),
		},
		{
			name: "GetThumbnailPath",
			action: func() string {
				return fullImageID.GetThumbnailPath()
			},
			want: filepath.Join("organizations", fullImageID.OrganizationID.String(), "workspaces", fullImageID.WorkspaceID.String(), "projects",
				fullImageID.ProjectID.String(), "dataset_storages", fullImageID.DatasetID.String(), fullImageID.ImageID.String()+"_thumbnail"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(_ *testing.T) {
			imagePath := tt.action()
			assert.Equal(t, tt.want, imagePath)
		})
	}
}
