package role

import (
	accErr "account_service/app/errors"
	"testing"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type MockRolesManager struct {
	mock.Mock
}

func (m *MockRolesManager) WriteSchema() error {
	args := m.Called()
	return args.Error(0)
}

func (m *MockRolesManager) WriteRelationship(relation string, subject *v1.SubjectReference, resource *v1.ObjectReference, operation v1.RelationshipUpdate_Operation) error {
	args := m.Called(relation, subject, resource, operation)
	return args.Error(0)
}

func (m *MockRolesManager) GetUserAllRelationships(userID string) ([]*v1.Relationship, error) {
	args := m.Called(userID)
	return args.Get(0).([]*v1.Relationship), args.Error(1)
}

func (m *MockRolesManager) CheckRelationshipToDelete(relationship *v1.Relationship, relation string) (bool, error) {
	args := m.Called(relationship, relation)
	return args.Bool(0), args.Error(1)
}

func (m *MockRolesManager) ChangeUserRelation(userID, orgID string, relations []string, resource string, operation v1.RelationshipUpdate_Operation) error {
	args := m.Called(userID, orgID, relations, resource, operation)
	return args.Error(0)
}

func (m *MockRolesManager) GetOrganizationRelationships(orgID string, relation string) ([]*v1.Relationship, error) {
	args := m.Called(orgID, relation)
	return args.Get(0).([]*v1.Relationship), args.Error(1)
}

func (m *MockRolesManager) GetRelationships(filter *v1.RelationshipFilter) ([]*v1.Relationship, error) {
	args := m.Called(filter)
	return args.Get(0).([]*v1.Relationship), args.Error(1)
}

func TestRoleService_IsLastOrgAdmin(t *testing.T) {
	mockRolesMgr := new(MockRolesManager)
	service := &roleService{RolesMgr: mockRolesMgr}

	orgID := "org1"
	userID := "user1"
	relationship := v1.Relationship{
		Relation: "organization_admin",
		Resource: &v1.ObjectReference{
			ObjectId: orgID,
		},
		Subject: &v1.SubjectReference{
			Object: &v1.ObjectReference{
				ObjectType: "user",
				ObjectId:   userID,
			},
		},
	}
	relationships := []*v1.Relationship{&relationship}
	mockRolesMgr.On("GetOrganizationRelationships", orgID, "organization_admin").Return(relationships, nil)

	isLastAdmin, err := service.IsLastOrgAdmin(orgID, userID)

	assert.NoError(t, err)
	assert.True(t, isLastAdmin)
}

func TestRoleService_IsLastOrgAdmin_NoAdmin(t *testing.T) {
	mockRolesMgr := new(MockRolesManager)
	service := &roleService{RolesMgr: mockRolesMgr}

	orgID := "org1"
	userID := "user1"
	var relationships []*v1.Relationship
	mockRolesMgr.On("GetOrganizationRelationships", orgID, "organization_admin").Return(relationships, nil)

	isLastAdmin, err := service.IsLastOrgAdmin(orgID, userID)

	assert.NoError(t, err)
	assert.False(t, isLastAdmin)
}

func TestRoleService_IsLastOrgAdmin_ManyAdmins(t *testing.T) {
	mockRolesMgr := new(MockRolesManager)
	service := &roleService{RolesMgr: mockRolesMgr}

	orgID := "org1"
	userID := "user1"
	relationship1 := v1.Relationship{
		Relation: "organization_admin",
		Resource: &v1.ObjectReference{
			ObjectId: orgID,
		},
		Subject: &v1.SubjectReference{
			Object: &v1.ObjectReference{
				ObjectType: "user",
				ObjectId:   userID,
			},
		},
	}
	relationship2 := v1.Relationship{
		Relation: "organization_admin",
		Resource: &v1.ObjectReference{
			ObjectId: orgID,
		},
		Subject: &v1.SubjectReference{
			Object: &v1.ObjectReference{
				ObjectType: "user",
				ObjectId:   "user2",
			},
		},
	}
	relationships := []*v1.Relationship{&relationship1, &relationship2}
	mockRolesMgr.On("GetOrganizationRelationships", orgID, "organization_admin").Return(relationships, nil)

	isLastAdmin, err := service.IsLastOrgAdmin(orgID, userID)

	assert.NoError(t, err)
	assert.False(t, isLastAdmin)
}

func TestRoleService_DeleteUserRelations(t *testing.T) {
	mockRolesMgr := new(MockRolesManager)
	service := &roleService{RolesMgr: mockRolesMgr}

	orgID := "org1"
	userID := "user1"
	relationship := v1.Relationship{
		Relation: "organization_admin",
		Resource: &v1.ObjectReference{
			ObjectId: orgID,
		},
		Subject: &v1.SubjectReference{
			Object: &v1.ObjectReference{
				ObjectType: "user",
				ObjectId:   userID,
			},
		},
	}
	userRelationships := []*v1.Relationship{&relationship}

	t.Run("Success", func(t *testing.T) {
		mockRolesMgr.On("GetUserAllRelationships", userID).Return(userRelationships, nil)
		mockRolesMgr.On("CheckRelationshipToDelete", &relationship, orgID).Return(true, nil)
		mockRolesMgr.On("ChangeUserRelation", relationship.Resource.ObjectType, relationship.Resource.ObjectId, []string{relationship.Relation}, userID, v1.RelationshipUpdate_OPERATION_DELETE).Return(nil)

		err := service.DeleteUserRelations(orgID, userID)
		assert.NoError(t, err)
		mockRolesMgr.AssertExpectations(t)
	})

	t.Run("GetUserAllRelationshipsError", func(t *testing.T) {
		mockRolesMgr := new(MockRolesManager)
		service := &roleService{RolesMgr: mockRolesMgr}

		orgID := "org1"
		userID := "user1"

		mockRolesMgr.On("GetUserAllRelationships", userID).Return([]*v1.Relationship{}, accErr.NewUnknownError("unexpected error"))

		err := service.DeleteUserRelations(orgID, userID)

		assert.Error(t, err)
		assert.Equal(t, "unexpected error", err.Error())
		mockRolesMgr.AssertExpectations(t)
	})

	t.Run("CheckRelationshipToDeleteError", func(t *testing.T) {
		mockRolesMgr := new(MockRolesManager)
		service := &roleService{RolesMgr: mockRolesMgr}

		orgID := "org1"
		userID := "user1"
		mockRolesMgr.On("GetUserAllRelationships", userID).Return(userRelationships, nil)
		mockRolesMgr.On("CheckRelationshipToDelete", &relationship, orgID).Return(false, accErr.NewUnknownError("unexpected error"))

		err := service.DeleteUserRelations(orgID, userID)
		assert.Error(t, err)
		assert.Equal(t, "unexpected error", err.Error())
		mockRolesMgr.AssertExpectations(t)
	})

	t.Run("ChangeUserRelationError", func(t *testing.T) {
		mockRolesMgr := new(MockRolesManager)
		service := &roleService{RolesMgr: mockRolesMgr}

		orgID := "org1"
		userID := "user1"
		mockRolesMgr.On("GetUserAllRelationships", userID).Return(userRelationships, nil)
		mockRolesMgr.On("CheckRelationshipToDelete", &relationship, orgID).Return(true, nil)
		mockRolesMgr.On("ChangeUserRelation", relationship.Resource.ObjectType, relationship.Resource.ObjectId, []string{relationship.Relation}, userID, v1.RelationshipUpdate_OPERATION_DELETE).Return(accErr.NewUnknownError("unexpected error"))

		err := service.DeleteUserRelations(orgID, userID)
		assert.Error(t, err)
		assert.Equal(t, "unexpected error", err.Error())
		mockRolesMgr.AssertExpectations(t)
	})
}
