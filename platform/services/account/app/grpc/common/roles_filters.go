// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package common

import (
	"fmt"

	"account_service/app/config"
	"account_service/app/roles"

	"geti.com/account_service_grpc/pb"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

func RelationshipsToUserRoles(userRelationships []*v1.Relationship) []*pb.UserRole {
	var userRoles []*pb.UserRole
	for _, relationship := range userRelationships {
		logger.Debugf("Checking relationship %v", relationship)
		userRoles = append(userRoles, &pb.UserRole{
			Role:         relationship.Relation,
			ResourceType: relationship.Resource.ObjectType,
			ResourceId:   relationship.Resource.ObjectId,
		})
	}
	return userRoles
}

func HasRole(roles []*pb.UserRole, roleName string, resourceTypes []string, resourceId string) bool {
	for _, role := range roles {
		logger.Debugf("Checking if role %v meets user find request criteria", role)
		if len(resourceTypes) > 0 {
			isResourceTypeMatched := false
			for _, resourceType := range resourceTypes {
				if role.ResourceType == resourceType {
					isResourceTypeMatched = true
				}
			}
			if !isResourceTypeMatched {
				logger.Debugf("Skipping role - resource type %v is not wanted", role.ResourceType)
				continue
			}
		}
		if resourceId != "" && resourceId != role.ResourceId {
			logger.Debugf("Skipping role - resource id %v is not wanted", role.ResourceId)
			continue
		}
		if roleName != "" && roleName != role.Role {
			logger.Debugf("Skipping role - role name %v is not wanted", role.Role)
			continue
		}
		logger.Debugf("Found wanted role - returning true for %v", role)
		return true
	}
	logger.Debug("All roles checked, user does not have wanted role")
	return false
}

func FilterRolesByCurrentUserPermissions(currentUserID string, rolesToFilter []*pb.UserRole) ([]*pb.UserRole, error) {
	var filteredRoles []*pb.UserRole

	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize client: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	currentUserRelationships, err := rolesMgr.GetUserAllRelationships(currentUserID)
	if err != nil {
		logger.Errorf("couldn't get relationships for the user %s: %v", currentUserID, err)
		return nil, err
	}

	currentUserRoles := RelationshipsToUserRoles(currentUserRelationships)

	for _, role := range rolesToFilter {
		roleResourceType := role.GetResourceType()

		if roleResourceType == "workspace" || roleResourceType == "organization" {
			resourceAdminRoleName := fmt.Sprintf("%s_%s", roleResourceType, "admin")
			resourceContributorRoleName := fmt.Sprintf("%s_%s", roleResourceType, "contributor")

			if HasRole(currentUserRoles, resourceAdminRoleName, []string{roleResourceType}, role.GetResourceId()) ||
				HasRole(currentUserRoles, resourceContributorRoleName, []string{roleResourceType}, role.GetResourceId()) {
				filteredRoles = append(filteredRoles, role)
			}
		} else if roleResourceType == "project" {
			resourceManagerRoleName := fmt.Sprintf("%s_%s", roleResourceType, "manager")
			resourceContributorRoleName := fmt.Sprintf("%s_%s", roleResourceType, "contributor")

			if HasRole(currentUserRoles, resourceManagerRoleName, []string{roleResourceType}, role.GetResourceId()) ||
				HasRole(currentUserRoles, resourceContributorRoleName, []string{roleResourceType}, role.GetResourceId()) {
				filteredRoles = append(filteredRoles, role)
				continue
			}

			projectId := role.GetResourceId()
			parentWorkspaceID, err := rolesMgr.GetProjectParentWorkspaceID(projectId)
			if err != nil {
				logger.Errorf("unable to get parent workspace for the project %s: %v", projectId, err)
				continue
			}

			if HasRole(currentUserRoles, "workspace_admin", []string{"workspace"}, parentWorkspaceID) {
				filteredRoles = append(filteredRoles, role)
			}

			parentOrganizationID, err := rolesMgr.GetWorkspaceParentOrganizationID(parentWorkspaceID)
			if err != nil {
				logger.Errorf("unable to get parent organization for the workspace %s: %v", parentWorkspaceID, err)
				continue
			}

			if HasRole(currentUserRoles, "organization_admin", []string{"organization"}, parentOrganizationID) {
				filteredRoles = append(filteredRoles, role)
			}
		}
	}

	return filteredRoles, nil
}
