// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package roles

import (
	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
)

func (m *RolesManager) ChangeOrganizationRelation(
	resourceType string,
	resourceID string,
	relations []string,
	organizationID string,
	operation v1.RelationshipUpdate_Operation) error {

	userSubject := v1.SubjectReference{
		Object: &v1.ObjectReference{
			ObjectType: "organization",
			ObjectId:   organizationID,
		},
	}

	resource := v1.ObjectReference{
		ObjectType: resourceType,
		ObjectId:   resourceID,
	}

	for _, relation := range relations {
		err := m.WriteRelationship(relation, &userSubject, &resource, operation)
		if err != nil {
			return err
		}
	}
	return nil
}
