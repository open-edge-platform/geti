// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package roles

import (
	"errors"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
)

func (m *RolesManager) GetProjectParentWorkspaceID(projectID string) (string, error) {
	filter := v1.RelationshipFilter{
		ResourceType:       "project",
		OptionalResourceId: projectID,
		OptionalRelation:   "parent_workspace",
	}

	relationships, err := m.GetRelationships(&filter)
	if err != nil {
		return "", err
	}

	if len(relationships) < 1 {
		return "", errors.New("no parent workspace")
	}

	return relationships[0].Subject.Object.ObjectId, nil
}
