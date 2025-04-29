// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package roles

import (
	"context"
	"encoding/base64"
	"fmt"
	"io"
	"time"

	"account_service/app/common/utils"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
)

var supportedUserResourceTypes = [...]string{"workspace", "project", "organization"}

var logger = utils.InitializeLogger()

func (m *RolesManager) ChangeUserRelation(resourceType string, resourceID string, relations []string, userID string, operation v1.RelationshipUpdate_Operation) error {
	_, err := base64.StdEncoding.DecodeString(userID)
	if err != nil {
		// If there's an error in decoding, userID is not in base64
		userID = base64.StdEncoding.EncodeToString([]byte(userID))
	}
	userSubject := v1.SubjectReference{
		Object: &v1.ObjectReference{
			ObjectType: "user",
			ObjectId:   userID,
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

func (m *RolesManager) AddServiceAccountToUser(userID string, serviceAccountID string) error {
	_, err := base64.StdEncoding.DecodeString(userID)
	if err != nil {
		userID = base64.StdEncoding.EncodeToString([]byte(userID))
	}
	userResource := &v1.ObjectReference{
		ObjectType: "user",
		ObjectId:   userID,
	}

	_, err = base64.StdEncoding.DecodeString(serviceAccountID)
	if err != nil {
		serviceAccountID = base64.StdEncoding.EncodeToString([]byte(serviceAccountID))
	}
	serviceAccountSubject := &v1.SubjectReference{
		Object: &v1.ObjectReference{
			ObjectType: "service_account",
			ObjectId:   serviceAccountID,
		},
	}

	return m.WriteRelationship("service_accounts", serviceAccountSubject, userResource, v1.RelationshipUpdate_OPERATION_TOUCH)
}

func (m *RolesManager) DeleteServiceAccountFromUser(userID string, serviceAccountID string) error {
	_, err := base64.StdEncoding.DecodeString(userID)
	if err != nil {
		userID = base64.StdEncoding.EncodeToString([]byte(userID))
	}
	userResource := &v1.ObjectReference{
		ObjectType: "user",
		ObjectId:   userID,
	}

	_, err = base64.StdEncoding.DecodeString(serviceAccountID)
	if err != nil {
		serviceAccountID = base64.StdEncoding.EncodeToString([]byte(serviceAccountID))
	}
	serviceAccountSubject := &v1.SubjectReference{
		Object: &v1.ObjectReference{
			ObjectType: "service_account",
			ObjectId:   serviceAccountID,
		},
	}

	return m.WriteRelationship("service_accounts", serviceAccountSubject, userResource, v1.RelationshipUpdate_OPERATION_DELETE)
}

func (m *RolesManager) GetAdminSubjectUsers() ([]string, error) {
	req := &v1.LookupSubjectsRequest{
		Resource: &v1.ObjectReference{
			ObjectType: "user_directory",
			ObjectId:   "global",
		},
		Permission:        "admin",
		SubjectObjectType: "user",
	}
	ctx := context.Background()
	stream, err := m.client.LookupSubjects(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to lookup resources: %w", err)
	}

	var adminUsers []string
	for {
		resp, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("error receiving lookup results %w", err)
		}
		if resp.Subject != nil {
			adminUsers = append(adminUsers, resp.Subject.SubjectObjectId)
		}
	}

	return adminUsers, nil
}

func (m *RolesManager) DeleteUserDirectory() error {
	userDirectory := &v1.ObjectReference{ObjectType: "user_directory", ObjectId: "global"}
	adminUsers, err := m.GetAdminSubjectUsers()
	if err != nil {
		return err
	}
	for _, userId := range adminUsers {
		userSubject := &v1.SubjectReference{
			Object: &v1.ObjectReference{
				ObjectType: "user",
				ObjectId:   userId,
			}}
		err := m.WriteRelationship("admin", userSubject, userDirectory, v1.RelationshipUpdate_OPERATION_DELETE)
		if err != nil {
			return err
		}
	}
	return nil
}

func (m *RolesManager) GetUserRelationships(userID string, resourceType string) ([]*v1.Relationship, error) {
	_, err := base64.StdEncoding.DecodeString(userID)
	if err != nil {
		// If there's an error in decoding, userID is not in base64
		userID = base64.StdEncoding.EncodeToString([]byte(userID))
	}
	filter := v1.RelationshipFilter{
		ResourceType: resourceType,
		OptionalSubjectFilter: &v1.SubjectFilter{
			SubjectType:       "user",
			OptionalSubjectId: userID,
		},
	}

	relationships, err := m.GetRelationships(&filter)
	if err != nil {
		return relationships, err
	}

	for index, relationship := range relationships {
		decodedUserId, err := base64.StdEncoding.DecodeString(relationship.Subject.Object.ObjectId)
		if err != nil {
			return nil, err
		}
		relationships[index].Subject.Object.ObjectId = string(decodedUserId)
	}
	return relationships, nil
}

func (m *RolesManager) GetOrganizationRelationships(orgID string, relation string) ([]*v1.Relationship, error) {
	filter := v1.RelationshipFilter{
		ResourceType:       "organization",
		OptionalRelation:   relation,
		OptionalResourceId: orgID,
	}

	relationships, err := m.GetRelationships(&filter)
	if err != nil {
		return relationships, err
	}

	for index, relationship := range relationships {
		decodedUserId, err := base64.StdEncoding.DecodeString(relationship.Subject.Object.ObjectId)
		if err != nil {
			return nil, err
		}
		relationships[index].Subject.Object.ObjectId = string(decodedUserId)
	}
	return relationships, nil
}

func (m *RolesManager) GetRelationshipsByOrganization(organizationID string, resource_type string) ([]*v1.Relationship, error) {
	filter := v1.RelationshipFilter{
		ResourceType: resource_type,
		OptionalSubjectFilter: &v1.SubjectFilter{
			SubjectType:       "organization",
			OptionalSubjectId: organizationID,
		},
	}

	relationships, err := m.GetRelationships(&filter)
	if err != nil {
		return relationships, err
	}
	return relationships, nil
}

func (m *RolesManager) GetUserAllRelationships(userID string) ([]*v1.Relationship, error) {
	var userRelationships []*v1.Relationship

	for _, resourceType := range supportedUserResourceTypes {
		retries := 0 // Reset retries for each resource type

		for retries <= 3 {
			relationships, err := m.GetUserRelationships(userID, resourceType)
			if err == nil {
				userRelationships = append(userRelationships, relationships...)
				break // Success - break inner loop
			}
			logger.Warnf("Error during role retrieval. Retries: %v. More details: %v", retries, err)
			retries++
			if retries > 3 {
				return userRelationships, fmt.Errorf("failed to get relationships for resource type %s after %d retries: %w",
					resourceType, retries, err)
			}
			time.Sleep(time.Second)
		}
	}

	return userRelationships, nil
}

func (m *RolesManager) CheckRelationshipToDelete(relationship *v1.Relationship, orgID string) (bool, error) {
	switch relationship.Resource.ObjectType {
	case "organization":
		return relationship.Resource.ObjectId == orgID, nil
	case "workspace":
		workspaceOrgID, err := m.GetWorkspaceParentOrganizationID(relationship.Resource.ObjectId)
		if err != nil {
			return false, err
		}
		return workspaceOrgID == orgID, nil
	case "project":
		projectWorkspaceID, err := m.GetProjectParentWorkspaceID(relationship.Resource.ObjectId)
		if err != nil {
			return false, err
		}
		workspaceOrgID, err := m.GetWorkspaceParentOrganizationID(projectWorkspaceID)
		if err != nil {
			return false, err
		}
		return workspaceOrgID == orgID, nil
	default:
		return false, nil
	}
}

func (m *RolesManager) GetUserOrganization(organizationID string, userID string) ([]*v1.Relationship, error) {
	_, err := base64.StdEncoding.DecodeString(userID)
	if err != nil {
		// If there's an error in decoding, userID is not in base64
		userID = base64.StdEncoding.EncodeToString([]byte(userID))
	}

	filter := v1.RelationshipFilter{
		ResourceType:       "organization",
		OptionalResourceId: organizationID,
		OptionalSubjectFilter: &v1.SubjectFilter{
			SubjectType:       "user",
			OptionalSubjectId: userID,
		},
	}

	relationships, err := m.GetRelationships(&filter)
	if err != nil {
		return relationships, err
	}
	return relationships, nil
}

func (m *RolesManager) GetUserOrgWorkspaces(organizationID string, userID string) ([]*v1.Relationship, error) {
	var relationships []*v1.Relationship
	userWorkspaceRelationships, err := m.GetUserRelationships(userID, "workspace")
	if err != nil {
		return relationships, err
	}

	orgWorkspaceRelationships, err := m.GetRelationshipsByOrganization(organizationID, "workspace")
	if err != nil {
		return relationships, err
	}

	orgWorkspaceMap := make(map[string]bool)
	for _, orgRel := range orgWorkspaceRelationships {
		orgWorkspaceMap[orgRel.Resource.ObjectId] = true
	}

	// Find common relationships
	for _, userRel := range userWorkspaceRelationships {
		if orgWorkspaceMap[userRel.Resource.ObjectId] {
			relationships = append(relationships, userRel)
		}
	}
	return relationships, nil
}

func (m *RolesManager) GetUserOrgProjects(organizationID string, userID string, orgWorkspaceRelationships []*v1.Relationship) ([]*v1.Relationship, error) {
	var relationships []*v1.Relationship
	userProjectRelationships, err := m.GetUserRelationships(userID, "project")
	if err != nil {
		return relationships, err
	}

	filter := v1.RelationshipFilter{
		ResourceType: "project",
		OptionalSubjectFilter: &v1.SubjectFilter{
			SubjectType: "workspace",
		},
	}
	workspaceProjectRelationships, err := m.GetRelationships(&filter)
	if err != nil {
		return relationships, err
	}

	orgWorkspaceMap := make(map[string]bool)
	for _, orgWorkspace := range orgWorkspaceRelationships {
		orgWorkspaceMap[orgWorkspace.Resource.ObjectId] = true
	}

	// Filter workspace project relationships related to the organization
	var orgProjectRelationships []*v1.Relationship
	for _, workspaceProjRel := range workspaceProjectRelationships {
		if orgWorkspaceMap[workspaceProjRel.Subject.Object.ObjectId] {
			orgProjectRelationships = append(orgProjectRelationships, workspaceProjRel)
		}
	}

	userProjectMap := make(map[string]*v1.Relationship)
	for _, userProjectRel := range userProjectRelationships {
		userProjectMap[userProjectRel.Resource.ObjectId] = userProjectRel
	}

	// Find the intersection of orgProjectRelationships and userProjectRelationships
	for _, orgProjectRel := range orgProjectRelationships {
		if userRel, exists := userProjectMap[orgProjectRel.Resource.ObjectId]; exists {
			relationships = append(relationships, userRel)
		}
	}

	return relationships, nil
}

func (m *RolesManager) GetUserAllRelationshipsByOrganization(organizationID string, userID string) ([]*v1.Relationship, error) {
	var relationships []*v1.Relationship
	userOrganizationRelationships, err := m.GetUserOrganization(organizationID, userID)
	if err != nil {
		return relationships, err
	}
	relationships = append(relationships, userOrganizationRelationships...)

	workspaceRelationships, err := m.GetUserOrgWorkspaces(organizationID, userID)
	if err != nil {
		return relationships, err
	}
	relationships = append(relationships, workspaceRelationships...)

	projectRelationships, err := m.GetUserOrgProjects(organizationID, userID, workspaceRelationships)
	if err != nil {
		return relationships, err
	}
	relationships = append(relationships, projectRelationships...)

	return relationships, nil
}
