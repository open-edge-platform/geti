// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"geti.com/account_service_grpc/pb"

	"strings"
)

// Function updates a list of roles with missing workspace roles - if it contains organization roles only
// it returns a list with workspace counterparts added
func UpdateMissingWorkspaceRoles(roleOperations []*pb.UserRoleOperation, defaultWorkspace string) []*pb.UserRoleOperation {
	addOrgAdmin := false
	addOrgAdminOperation := ""
	addOrgContributor := false
	addOrgContributorOperation := ""

	for _, role := range roleOperations {
		if strings.Contains(role.Role.Role, "organization_admin") {
			addOrgAdmin = true
			addOrgAdminOperation = role.Operation
		} else if strings.Contains(role.Role.Role, "organization_contributor") {
			addOrgContributor = true
			addOrgContributorOperation = role.Operation
		} else if strings.Contains(role.Role.Role, "workspace_admin") {
			addOrgAdmin = false
			break
		} else if strings.Contains(role.Role.Role, "workspace_contributor") {
			addOrgContributor = false
			break
		}
	}

	if addOrgAdmin || addOrgContributor {
		workspaceRole := "workspace_admin"
		workspaceOperation := addOrgAdminOperation
		if addOrgContributor {
			workspaceRole = "workspace_contributor"
			workspaceOperation = addOrgContributorOperation
		}
		roleOperations = append(roleOperations, &pb.UserRoleOperation{
			Operation: workspaceOperation,
			Role: &pb.UserRole{
				Role:         workspaceRole,
				ResourceType: "workspace",
				ResourceId:   defaultWorkspace,
			},
		})
	}

	return roleOperations
}
