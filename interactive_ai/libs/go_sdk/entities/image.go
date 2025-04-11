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
)

// FullImageID represents full path to the image
type FullImageID struct {
	ContextID

	ImageID ID
}

// NewFullImageID creates new FullImageID instance
func NewFullImageID(organizationID string, workspaceID string, projectID string, datasetID string, imageID string) *FullImageID {
	return &FullImageID{
		ContextID: ContextID{
			OrganizationID: ID{organizationID},
			WorkspaceID:    ID{workspaceID},
			ProjectID:      ID{projectID},
			DatasetID:      ID{datasetID},
		},
		ImageID: ID{imageID},
	}
}

// GetPath construct the path to the image based on IDs
func (iid FullImageID) GetPath() string {
	return filepath.Join("organizations", iid.OrganizationID.String(), "workspaces", iid.WorkspaceID.String(), "projects",
		iid.ProjectID.String(), "dataset_storages", iid.DatasetID.String(), iid.ImageID.String())
}

// GetThumbnailPath construct the path to the image thumbnail based on IDs
func (iid FullImageID) GetThumbnailPath() string {
	return iid.GetPath() + "_thumbnail"
}
