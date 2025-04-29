package utils

import (
	"testing"

	"geti.com/account_service_grpc/pb"
	"github.com/stretchr/testify/assert"
)

func TestUpdateMissingWorkspaceRoles(t *testing.T) {
	t.Run("Test with organization_admin role", func(t *testing.T) {
		roleOperations := []*pb.UserRoleOperation{
			{
				Operation: "CREATE",
				Role: &pb.UserRole{
					Role:         "organization_admin",
					ResourceType: "organization",
					ResourceId:   "org123",
				},
			},
		}

		extendedRoles := UpdateMissingWorkspaceRoles(roleOperations, "workspace123")
		assert.NotNil(t, extendedRoles)
		assert.Equal(t, 2, len(extendedRoles))
		assert.Equal(t, "org123", extendedRoles[0].Role.ResourceId)
		assert.Equal(t, "organization_admin", extendedRoles[0].Role.Role)
		assert.Equal(t, "organization", extendedRoles[0].Role.ResourceType)
		assert.Equal(t, "CREATE", extendedRoles[0].Operation)
		assert.Equal(t, "workspace123", extendedRoles[1].Role.ResourceId)
		assert.Equal(t, "workspace_admin", extendedRoles[1].Role.Role)
		assert.Equal(t, "workspace", extendedRoles[1].Role.ResourceType)
		assert.Equal(t, "CREATE", extendedRoles[1].Operation)
	})

	t.Run("Test with organization_contributor role", func(t *testing.T) {
		roleOperations := []*pb.UserRoleOperation{
			{
				Operation: "CREATE",
				Role: &pb.UserRole{
					Role:         "organization_contributor",
					ResourceType: "organization",
					ResourceId:   "org123",
				},
			},
		}

		extendedRoles := UpdateMissingWorkspaceRoles(roleOperations, "workspace123")
		assert.NotNil(t, extendedRoles)
		assert.Equal(t, 2, len(extendedRoles))
		assert.Equal(t, "org123", extendedRoles[0].Role.ResourceId)
		assert.Equal(t, "organization_contributor", extendedRoles[0].Role.Role)
		assert.Equal(t, "organization", extendedRoles[0].Role.ResourceType)
		assert.Equal(t, "CREATE", extendedRoles[0].Operation)
		assert.Equal(t, "workspace123", extendedRoles[1].Role.ResourceId)
		assert.Equal(t, "workspace_contributor", extendedRoles[1].Role.Role)
		assert.Equal(t, "workspace", extendedRoles[1].Role.ResourceType)
		assert.Equal(t, "CREATE", extendedRoles[1].Operation)
	})

	t.Run("Test with workspace role", func(t *testing.T) {
		roleOperations := []*pb.UserRoleOperation{
			{
				Operation: "CREATE",
				Role: &pb.UserRole{
					Role:         "workspace_contributor",
					ResourceType: "workspace",
					ResourceId:   "workspace123",
				},
			},
		}

		extendedRoles := UpdateMissingWorkspaceRoles(roleOperations, "workspace123")
		assert.NotNil(t, extendedRoles)
		assert.Equal(t, 1, len(extendedRoles))
		assert.Equal(t, "workspace123", extendedRoles[0].Role.ResourceId)
		assert.Equal(t, "workspace_contributor", extendedRoles[0].Role.Role)
		assert.Equal(t, "CREATE", extendedRoles[0].Operation)
		assert.Equal(t, "workspace", extendedRoles[0].Role.ResourceType)
	})
}
