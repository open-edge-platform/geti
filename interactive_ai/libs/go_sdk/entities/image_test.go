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
