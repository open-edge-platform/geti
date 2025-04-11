package organization

import (
	"context"
	"testing"

	"account_service/app/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type MockOrganizationRepository struct {
	mock.Mock
}

type MockRoleService struct {
	mock.Mock
}

func (m *MockRoleService) DeleteUserRelations(orgId string, userId string) error {
	args := m.Called(orgId, userId)
	return args.Error(0)
}

func (m *MockRoleService) IsLastOrgAdmin(orgId string, userId string) (bool, error) {
	args := m.Called(orgId, userId)
	return args.Bool(0), args.Error(1)
}

func (m *MockOrganizationRepository) GetOrg(ctx context.Context, orgId string) (models.Organization, error) {
	args := m.Called(ctx, orgId)
	return args.Get(0).(models.Organization), args.Error(1)
}

func TestOrganizationService_CheckIfLastRegisteredOrgAdmin_Success(t *testing.T) {
	ctx := context.Background()
	mockRepo := new(MockOrganizationRepository)
	mockRoleService := new(MockRoleService)
	service := &organizationService{repo: mockRepo, RoleService: mockRoleService}

	orgId := "org123"
	userId := "user123"

	mockRoleService.On("IsLastOrgAdmin", orgId, userId).Return(true, nil)
	mockRepo.On("GetOrg", ctx, orgId).Return(models.Organization{Status: "RGS"}, nil)

	err := service.CheckIfLastRegisteredOrgAdmin(ctx, orgId, userId)
	assert.NoError(t, err)
	mockRepo.AssertExpectations(t)
	mockRoleService.AssertExpectations(t)
}
