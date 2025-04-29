// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package role

import (
	"account_service/app/common/utils"
	"account_service/app/config"
	accErr "account_service/app/errors"
	"account_service/app/roles"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type Service struct {
}

var logger = utils.InitializeLogger()

func GetUserAllRelationshipsByOrganization(orgId string, userId string) ([]*v1.Relationship, error) {
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("Unable to initialize roles manager: %v", err)
		return nil, status.Error(codes.Internal, "unexpected error")
	}

	// Fetch all user relationships within the organization
	userRelationships, err := rolesMgr.GetUserAllRelationshipsByOrganization(orgId, userId)
	if err != nil {
		logger.Errorf("Unable to get user relationships: %v", err)
		return nil, status.Error(codes.Internal, "unexpected error")
	}
	return userRelationships, nil
}

func CreateRole(resourceType string, resourceId string, role string, userId string) error {
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("Unable to initialize roles manager: %v", err)
		return status.Error(codes.Internal, "unexpected error")
	}

	err = rolesMgr.ChangeUserRelation(resourceType, resourceId, []string{role}, userId, v1.RelationshipUpdate_OPERATION_TOUCH)
	if err != nil {
		logger.Errorf("Error assigning role: %v", err)
		return status.Error(codes.Internal, "unexpected error")
	}

	return nil
}

func DeleteRole(resourceType string, resourceId string, role string, userId string) error {
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("Unable to initialize roles manager: %v", err)
		return status.Error(codes.Internal, "unexpected error")
	}

	err = rolesMgr.ChangeUserRelation(resourceType, resourceId, []string{role}, userId, v1.RelationshipUpdate_OPERATION_DELETE)
	if err != nil {
		logger.Errorf("Error removing role: %v", err)
		return status.Error(codes.Internal, "unexpected error")
	}

	return nil
}

func DeleteConflictingRoles(newResourceType, newResourceId string, userId string, userRelationships []*v1.Relationship) error {
	for _, rel := range userRelationships {
		isDirectConflict := rel.Resource.ObjectType == newResourceType && rel.Resource.ObjectId == newResourceId
		// As per discussion, in case organization role is updated, we should match access level to the same level
		isWorkspaceConflict := newResourceType == "organization" && rel.Resource.ObjectType == "workspace"
		logger.Debugf("Working with %v. Checking if there is direct conflict: %v. Checking workspace conflict: %v", rel, isDirectConflict, isWorkspaceConflict)
		if isDirectConflict || isWorkspaceConflict {
			logger.Debugf("Removing conflicting role %s for user ID: %s on resource ID: %s", rel.Relation, userId, newResourceId)
			if err := DeleteRole(rel.Resource.ObjectType, rel.Resource.ObjectId, rel.Relation, userId); err != nil {
				return err
			}
		}
	}
	return nil
}

func IsValidRole(role string) bool {
	validRoles := map[string]struct{}{
		"organization_admin":       {},
		"organization_contributor": {},
		"workspace_admin":          {},
		"workspace_contributor":    {},
		"project_manager":          {},
		"project_contributor":      {},
	}
	_, valid := validRoles[role]
	return valid
}

type roleService struct {
	RolesMgr roles.IRolesManager
}

type IRoleService interface {
	IsLastOrgAdmin(orgId string, userId string) (bool, error)
	DeleteUserRelations(orgID string, userID string) error
}

func NewService(roleManager roles.IRolesManager) IRoleService {
	return &roleService{RolesMgr: roleManager}
}

func (s *roleService) IsLastOrgAdmin(orgID string, userID string) (bool, error) {
	adminsRelationships, err := s.RolesMgr.GetOrganizationRelationships(orgID, "organization_admin")
	if err != nil {
		logger.Errorf("error during getting organization admin relationships: %v", err)
		return false, accErr.NewInternalError("unexpected error")
	}

	return len(adminsRelationships) == 1 && adminsRelationships[0].Subject.Object.ObjectId == userID, nil
}

func (s *roleService) DeleteUserRelations(orgID string, userID string) error {
	userRelationships, err := s.RolesMgr.GetUserAllRelationships(userID)
	if err != nil {
		logger.Errorf("unable to get all user relationships: %v", err)
		return accErr.NewUnknownError("unexpected error")
	}

	for _, relationship := range userRelationships {
		deleteRelation, err := s.RolesMgr.CheckRelationshipToDelete(relationship, orgID)
		if err != nil {
			logger.Errorf("failed to determine if relationship should be deleted: %v", err)
			return accErr.NewUnknownError("unexpected error")
		}
		if deleteRelation {
			err := s.RolesMgr.ChangeUserRelation(relationship.Resource.ObjectType, relationship.Resource.ObjectId, []string{relationship.Relation}, userID, v1.RelationshipUpdate_OPERATION_DELETE)
			if err != nil {
				logger.Errorf("failed to delete user relationship: %v", err)
				return accErr.NewUnknownError("unexpected error")
			}
		}
	}
	return nil
}
