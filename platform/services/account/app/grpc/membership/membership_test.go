package membership

import (
	"account_service/app/models"
	"context"
	"errors"
	"testing"
	"time"

	"geti.com/account_service_grpc/pb"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
)

type MockMembershipService struct {
	mock.Mock
}

func (m *MockMembershipService) GetUserMemberships(ctx context.Context, req *pb.UserMembershipRequest) ([]models.UserMembershipResult, int64, error) {
	args := m.Called(ctx, req)
	return args.Get(0).([]models.UserMembershipResult), args.Get(1).(int64), args.Error(2)
}

func (m *MockMembershipService) SetUserStatus(ctx context.Context, userID uuid.UUID, organization_id uuid.UUID, status string) (*models.UserStatus, error) {
	args := m.Called(ctx, userID, organization_id, status)
	return args.Get(0).(*models.UserStatus), args.Error(1)
}

func (m *MockMembershipService) GetMemberships(ctx context.Context, req *pb.MembershipRequest) ([]models.MembershipResult, int64, error) {
	args := m.Called(ctx, req)
	return args.Get(0).([]models.MembershipResult), args.Get(1).(int64), args.Error(2)
}

func (m *MockMembershipService) DeleteMemberships(ctx context.Context, req *pb.DeleteMembershipRequest) (*emptypb.Empty, error) {
	args := m.Called(ctx, req)
	return args.Get(0).(*emptypb.Empty), args.Error(1)
}

func TestGRPCServer_GetMemberships(t *testing.T) {
	ctx := context.Background()

	t.Run("ServiceError", func(t *testing.T) {
		req := &pb.MembershipRequest{
			OrganizationId: "org-id",
		}

		mockService := new(MockMembershipService)
		mockService.On("GetMemberships", ctx, req).Return([]models.MembershipResult{}, int64(0), errors.New("service error"))

		server := &GRPCServer{Service: mockService}

		_, err := server.GetMemberships(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, codes.Internal, status.Code(err))
	})

	t.Run("Success", func(t *testing.T) {
		req := &pb.MembershipRequest{
			OrganizationId: "org-id",
		}

		mockService := new(MockMembershipService)
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
		mockService.On("GetMemberships", ctx, req).Return(memberships, int64(1), nil)

		server := &GRPCServer{Service: mockService}

		response, err := server.GetMemberships(ctx, req)
		assert.NoError(t, err)
		assert.Len(t, response.Memberships, 1)
		assert.Equal(t, "John", response.Memberships[0].FirstName)
		assert.Equal(t, int32(1), response.TotalMatchedCount)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		req := &pb.MembershipRequest{
			OrganizationId: "org-id",
		}

		mockService := new(MockMembershipService)
		mockService.On("GetMemberships", ctx, req).Return([]models.MembershipResult{}, int64(0), nil)

		server := &GRPCServer{Service: mockService}

		response, err := server.GetMemberships(ctx, req)
		assert.NoError(t, err)
		assert.Len(t, response.Memberships, 0)
		assert.Equal(t, int32(0), response.TotalMatchedCount)
	})
}

func TestGRPCServer_Modify(t *testing.T) {
	ctx := context.Background()

	t.Run("InvalidUserID", func(t *testing.T) {
		req := &pb.MembershipStatusRequest{
			UserId:         "invalid-uuid",
			OrganizationId: "org-id",
			Payload:        &pb.MembershipStatusPayload{Status: "ACT"},
		}

		mockService := new(MockMembershipService)
		server := &GRPCServer{Service: mockService}

		_, err := server.Modify(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, codes.InvalidArgument, status.Code(err))
	})

	t.Run("InvalidOrganizationID", func(t *testing.T) {
		req := &pb.MembershipStatusRequest{
			UserId:         uuid.New().String(),
			OrganizationId: "invalid-uuid",
			Payload:        &pb.MembershipStatusPayload{Status: "ACT"},
		}

		mockService := new(MockMembershipService)
		server := &GRPCServer{Service: mockService}

		_, err := server.Modify(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, codes.InvalidArgument, status.Code(err))
	})

	t.Run("Success", func(t *testing.T) {
		req := &pb.MembershipStatusRequest{
			UserId:         uuid.New().String(),
			OrganizationId: uuid.New().String(),
			Payload:        &pb.MembershipStatusPayload{Status: "ACT"},
		}

		userStatus := &models.UserStatus{
			ID:             uuid.New(),
			Status:         "ACTIVE",
			OrganizationID: uuid.New(),
			UserID:         uuid.New(),
			CreatedBy:      uuid.New().String(),
			CreatedAt:      time.Now(),
		}

		mockService := new(MockMembershipService)
		mockService.On("SetUserStatus", ctx, mock.Anything, mock.Anything, req.Payload.Status).Return(userStatus, nil)

		server := &GRPCServer{Service: mockService}

		response, err := server.Modify(ctx, req)
		assert.NoError(t, err)
		assert.Equal(t, userStatus.ID.String(), response.Id)
		assert.Equal(t, userStatus.Status, response.Status)
		assert.Equal(t, userStatus.OrganizationID.String(), response.OrganizationId)
		assert.Equal(t, userStatus.UserID.String(), response.UserId)
		assert.Equal(t, userStatus.CreatedBy, response.CreatedBy)
	})
}

func TestGRPCServer_GetUserMemberships(t *testing.T) {
	ctx := context.Background()

	t.Run("ServiceError", func(t *testing.T) {
		req := &pb.UserMembershipRequest{
			UserId: "user-id",
		}

		mockService := new(MockMembershipService)
		mockService.On("GetUserMemberships", ctx, req).Return([]models.UserMembershipResult{}, int64(0), errors.New("service error"))

		server := &GRPCServer{Service: mockService}

		_, err := server.GetUserMemberships(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, codes.Internal, status.Code(err))
	})

	t.Run("Success", func(t *testing.T) {
		req := &pb.UserMembershipRequest{
			UserId: "user-id",
		}

		mockService := new(MockMembershipService)
		memberships := []models.UserMembershipResult{
			{
				ID:               uuid.New(),
				OrganizationID:   uuid.New(),
				OrganizationName: "Dummy",
				Status:           "ACT",
				CreatedAt:        time.Now(),
			},
		}
		mockService.On("GetUserMemberships", ctx, req).Return(memberships, int64(1), nil)

		server := &GRPCServer{Service: mockService}

		response, err := server.GetUserMemberships(ctx, req)
		assert.NoError(t, err)
		assert.Len(t, response.Memberships, 1)
		assert.Equal(t, "Dummy", response.Memberships[0].OrganizationName)
		assert.Equal(t, int32(1), response.TotalMatchedCount)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		req := &pb.UserMembershipRequest{
			UserId: "user-id",
		}

		mockService := new(MockMembershipService)
		mockService.On("GetUserMemberships", ctx, req).Return([]models.UserMembershipResult{}, int64(0), nil)

		server := &GRPCServer{Service: mockService}

		response, err := server.GetUserMemberships(ctx, req)
		assert.NoError(t, err)
		assert.Len(t, response.Memberships, 0)
		assert.Equal(t, int32(0), response.TotalMatchedCount)
	})
}

func TestGRPCServer_DeleteMemberships(t *testing.T) {
	ctx := context.Background()
	userID := uuid.New().String()
	organizationID := uuid.New().String()

	t.Run("ServiceError", func(t *testing.T) {
		req := &pb.DeleteMembershipRequest{
			UserId:         userID,
			OrganizationId: organizationID,
		}

		mockService := new(MockMembershipService)
		mockService.On("DeleteMemberships", ctx, req).Return(&emptypb.Empty{}, errors.New("service error"))

		server := &GRPCServer{Service: mockService}

		_, err := server.DeleteMemberships(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, codes.InvalidArgument, status.Code(err))
	})

	t.Run("Success", func(t *testing.T) {
		req := &pb.DeleteMembershipRequest{
			UserId:         userID,
			OrganizationId: organizationID,
		}

		mockService := new(MockMembershipService)
		mockService.On("DeleteMemberships", ctx, req).Return(&emptypb.Empty{}, nil)

		server := &GRPCServer{Service: mockService}

		response, err := server.DeleteMemberships(ctx, req)
		assert.NoError(t, err)
		assert.NotNil(t, response)
	})
}
