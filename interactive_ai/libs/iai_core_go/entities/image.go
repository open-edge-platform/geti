// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"path/filepath"
)

// FullImageID represents full path to the image.
type FullImageID struct {
	ContextID

	ImageID ID
}

// NewFullImageID creates new FullImageID instance.
func NewFullImageID(
	organizationID string,
	workspaceID string,
	projectID string,
	datasetID string,
	imageID string,
) *FullImageID {
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

// GetPath construct the path to the image based on IDs.
func (iid FullImageID) GetPath() string {
	return filepath.Join(
		"organizations",
		iid.OrganizationID.String(),
		"workspaces",
		iid.WorkspaceID.String(),
		"projects",
		iid.ProjectID.String(),
		"dataset_storages",
		iid.DatasetID.String(),
		iid.ImageID.String(),
	)
}

// GetThumbnailPath construct the path to the image thumbnail based on IDs.
func (iid FullImageID) GetThumbnailPath() string {
	return iid.GetPath() + "_thumbnail"
}
