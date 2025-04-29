package membership

import (
	"account_service/app/models"
	"account_service/app/repository"
	"context"
	"errors"
	"testing"
	"time"

	proto "geti.com/account_service_grpc/pb"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"google.golang.org/protobuf/types/known/emptypb"
)

type MockOrganizationService struct {
	mock.Mock
}

type MockMembershipRepository struct {
	mock.Mock
}

type MockRoleService struct {
	mock.Mock
}

type MockPersonalAccessTokenRepository struct {
	mock.Mock
}

func (m *MockRoleService) IsLastOrgAdmin(orgID string, userID string) (bool, error) {
	args := m.Called(orgID, userID)
	return args.Bool(0), args.Error(1)
}

func (m *MockRoleService) DeleteUserRelations(orgID string, userID string) error {
	args := m.Called(orgID, userID)
	return args.Error(0)
}

func (m *MockOrganizationService) CheckIfLastRegisteredOrgAdmin(ctx context.Context, orgID string, userID string) error {
	args := m.Called(ctx, orgID, userID)
	return args.Error(0)
}

func (m *MockMembershipRepository) CreateUserMembership(ctx context.Context, userStatus *models.UserStatus) error {
	args := m.Called(ctx, userStatus)
	return args.Error(0)
}

func (m *MockMembershipRepository) FindMemberships(ctx context.Context, req *repository.MembershipQuery) ([]models.MembershipResult, int64, error) {
	args := m.Called(ctx, req)
	return args.Get(0).([]models.MembershipResult), args.Get(1).(int64), args.Error(2)
}

func (m *MockMembershipRepository) GetUserStatus(ctx context.Context, userID string, organizationID string) (*models.UserStatus, error) {
	args := m.Called(ctx, userID, organizationID)
	return args.Get(0).(*models.UserStatus), args.Error(1)
}

func (m *MockMembershipRepository) FindUserMemberships(ctx context.Context, req *repository.UserMembershipQuery) ([]models.UserStatus, int64, error) {
	args := m.Called(ctx, req)
	return args.Get(0).([]models.UserStatus), args.Get(1).(int64), args.Error(2)
}

func (m *MockMembershipRepository) SaveUserMembership(ctx context.Context, userStatus *models.UserStatus) error {
	args := m.Called(ctx, userStatus)
	return args.Error(0)
}

func (m *MockMembershipRepository) UpdatePersonalAccessTokenMembership(ctx context.Context, userID string, organizationID string, newStatus string) error {
	args := m.Called(ctx, userID, organizationID, newStatus)
	return args.Error(0)
}

func (m *MockMembershipRepository) FindMembershipsToDelete(ctx context.Context, userID string, organizationID string) (*[]models.UserStatus, error) {
	args := m.Called(ctx, userID, organizationID)
	return args.Get(0).(*[]models.UserStatus), args.Error(1)
}

func (m *MockMembershipRepository) DeleteMemberships(ctx context.Context, userID string, organizationID string, patRepo repository.PersonalAccessTokenRepository) (*emptypb.Empty, error) {
	args := m.Called(ctx, userID, organizationID, patRepo)
	return args.Get(0).(*emptypb.Empty), args.Error(1)
}

func (m *MockPersonalAccessTokenRepository) DeactivatePersonalAccessTokens(userID string, organizationID string) error {
	args := m.Called(userID, organizationID)
	return args.Error(0)
}

func TestMembershipService_GetMemberships(t *testing.T) {
	ctx := context.Background()

	t.Run("RepositoryError", func(t *testing.T) {
		query := repository.MembershipQuery{
			OrganizationId: "org-id",
		}
		req := &proto.MembershipRequest{
			OrganizationId: "org-id",
		}

		mockRepo := new(MockMembershipRepository)
		mockRepo.On("FindMemberships", ctx, &query).Return([]models.MembershipResult{}, int64(0), errors.New("repository error"))

		mockOrgService := new(MockOrganizationService)
		mockRoleService := new(MockRoleService)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		_, _, err := service.GetMemberships(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, "repository error", err.Error())
	})

	t.Run("Success", func(t *testing.T) {
		query := repository.MembershipQuery{
			OrganizationId: "org-id",
		}
		req := &proto.MembershipRequest{
			OrganizationId: "org-id",
		}

		mockRepo := new(MockMembershipRepository)
		memberships := []models.MembershipResult{
			{
				ID:         uuid.New(),
				UserID:     uuid.New(),
				FirstName:  "John",
				SecondName: "Doe",
				Email:      "john.doe@example.com",
				Status:     "ACT",
				CreatedAt:  time.Now(),
			},
		}
		mockRepo.On("FindMemberships", ctx, &query).Return(memberships, int64(1), nil)

		mockOrgService := new(MockOrganizationService)
		mockRoleService := new(MockRoleService)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		response, totalMatchedCount, err := service.GetMemberships(ctx, req)
		assert.NoError(t, err)
		assert.Equal(t, int64(1), totalMatchedCount)
		assert.Len(t, response, 1)
		assert.Equal(t, "John", response[0].FirstName)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		query := repository.MembershipQuery{
			OrganizationId: "org-id",
		}
		req := &proto.MembershipRequest{
			OrganizationId: "org-id",
		}

		mockRepo := new(MockMembershipRepository)
		mockRepo.On("FindMemberships", ctx, &query).Return([]models.MembershipResult{}, int64(0), nil)

		mockOrgService := new(MockOrganizationService)
		mockRoleService := new(MockRoleService)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		response, totalMatchedCount, err := service.GetMemberships(ctx, req)
		assert.NoError(t, err)
		assert.Equal(t, int64(0), totalMatchedCount)
		assert.Len(t, response, 0)
	})
}

func TestMembershipService_SetUserStatus(t *testing.T) {
	ctx := context.Background()
	userID := uuid.New()
	organizationID := uuid.New()

	t.Run("CreateUserMembershipError", func(t *testing.T) {
		query := repository.UserMembershipQuery{
			UserId:         userID.String(),
			OrganizationId: organizationID.String(),
		}
		mockRepo := new(MockMembershipRepository)
		memberships := []models.UserStatus{
			{
				ID:             uuid.New(),
				OrganizationID: organizationID,
				Organization:   models.Organization{Name: "Dummy"},
				Status:         "ACT",
				CreatedAt:      time.Now(),
			},
		}
		mockRepo.On("FindUserMemberships", ctx, &query).Return(memberships, int64(1), nil)
		mockRepo.On("SaveUserMembership", ctx, &memberships[0]).Return(nil)
		mockRepo.On("UpdatePersonalAccessTokenMembership", ctx, userID.String(), organizationID.String(), "ACT").Return(nil)
		mockRepo.On("SaveUserMembership", ctx, mock.Anything).Return(errors.New("unexpected error"))

		mockOrgService := new(MockOrganizationService)
		mockOrgService.On("CheckIfLastRegisteredOrgAdmin", ctx, organizationID.String(), userID.String()).Return(nil)
		mockRoleService := new(MockRoleService)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		_, err := service.SetUserStatus(ctx, userID, organizationID, "ACT")
		assert.Error(t, err)
		assert.Equal(t, "unexpected error", err.Error())
	})

	t.Run("Success", func(t *testing.T) {
		query := repository.UserMembershipQuery{
			UserId:         userID.String(),
			OrganizationId: organizationID.String(),
		}
		mockRepo := new(MockMembershipRepository)
		memberships := []models.UserStatus{
			{
				ID:             uuid.New(),
				OrganizationID: organizationID,
				Organization:   models.Organization{Name: "Dummy"},
				Status:         "ACT",
				CreatedAt:      time.Now(),
			},
		}
		mockRepo.On("FindUserMemberships", ctx, &query).Return(memberships, int64(1), nil)
		mockRepo.On("SaveUserMembership", ctx, &memberships[0]).Return(nil)
		mockRepo.On("UpdatePersonalAccessTokenMembership", ctx, userID.String(), organizationID.String(), "ACT").Return(nil)
		mockRepo.On("SaveUserMembership", ctx, mock.Anything).Return(nil)

		mockOrgService := new(MockOrganizationService)
		mockOrgService.On("CheckIfLastRegisteredOrgAdmin", ctx, organizationID.String(), userID.String()).Return(nil)
		mockRoleService := new(MockRoleService)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		newStatus, err := service.SetUserStatus(ctx, userID, organizationID, "ACT")
		assert.NoError(t, err)
		assert.Equal(t, "ACT", newStatus.Status)
		assert.Equal(t, userID, newStatus.UserID)
		assert.Equal(t, organizationID, newStatus.OrganizationID)
		assert.True(t, newStatus.Current)
	})
}

func TestMembershipService_GetUserMemberships(t *testing.T) {
	ctx := context.Background()

	t.Run("RepositoryError", func(t *testing.T) {
		query := repository.UserMembershipQuery{
			UserId: "user-id",
		}
		req := &proto.UserMembershipRequest{
			UserId: "user-id",
		}

		mockRepo := new(MockMembershipRepository)
		mockRepo.On("FindUserMemberships", ctx, &query).Return([]models.UserStatus{}, int64(0), errors.New("repository error"))

		mockOrgService := new(MockOrganizationService)
		mockRoleService := new(MockRoleService)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		_, _, err := service.GetUserMemberships(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, "repository error", err.Error())
	})

	t.Run("Success", func(t *testing.T) {
		query := repository.UserMembershipQuery{
			UserId: "user-id",
		}
		req := &proto.UserMembershipRequest{
			UserId: "user-id",
		}

		mockRepo := new(MockMembershipRepository)
		memberships := []models.UserStatus{
			{
				ID:               uuid.New(),
				OrganizationID:   uuid.New(),
				OrganizationName: "Dummy",
				Status:           "ACT",
				CreatedAt:        time.Now(),
			},
		}
		mockRepo.On("FindUserMemberships", ctx, &query).Return(memberships, int64(1), nil)

		mockOrgService := new(MockOrganizationService)
		mockRoleService := new(MockRoleService)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		response, totalMatchedCount, err := service.GetUserMemberships(ctx, req)
		assert.NoError(t, err)
		assert.Equal(t, int64(1), totalMatchedCount)
		assert.Len(t, response, 1)
		assert.Equal(t, "Dummy", response[0].OrganizationName)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		query := repository.UserMembershipQuery{
			UserId: "user-id",
		}
		req := &proto.UserMembershipRequest{
			UserId: "user-id",
		}

		mockRepo := new(MockMembershipRepository)
		mockRepo.On("FindUserMemberships", ctx, &query).Return([]models.UserStatus{}, int64(0), nil)

		mockOrgService := new(MockOrganizationService)
		mockRoleService := new(MockRoleService)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		response, totalMatchedCount, err := service.GetUserMemberships(ctx, req)
		assert.NoError(t, err)
		assert.Equal(t, int64(0), totalMatchedCount)
		assert.Len(t, response, 0)
	})
}

func TestMembershipService_DeleteMemberships(t *testing.T) {
	ctx := context.Background()
	userID := uuid.New().String()
	organizationID := uuid.New().String()

	t.Run("RepositoryError", func(t *testing.T) {
		req := &proto.DeleteMembershipRequest{
			UserId:         userID,
			OrganizationId: organizationID,
		}

		mockRepo := new(MockMembershipRepository)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		mockRepo.On("DeleteMemberships", ctx, userID, organizationID, mockPatRepo).Return(&emptypb.Empty{}, errors.New("repository error"))

		mockOrgService := new(MockOrganizationService)
		mockRoleService := new(MockRoleService)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		_, err := service.DeleteMemberships(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, "repository error", err.Error())
	})

	t.Run("Success", func(t *testing.T) {
		req := &proto.DeleteMembershipRequest{
			UserId:         userID,
			OrganizationId: organizationID,
		}

		mockRepo := new(MockMembershipRepository)
		mockPatRepo := new(MockPersonalAccessTokenRepository)
		mockRepo.On("DeleteMemberships", ctx, userID, organizationID, mockPatRepo).Return(&emptypb.Empty{}, nil)

		mockOrgService := new(MockOrganizationService)
		mockRoleService := new(MockRoleService)
		service := NewMembershipService(mockRepo, mockPatRepo, mockOrgService, mockRoleService)

		response, err := service.DeleteMemberships(ctx, req)
		assert.NoError(t, err)
		assert.NotNil(t, response)
	})
}
