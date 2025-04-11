// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package user

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
)

type MockUserService struct {
	mock.Mock
}

func (m *MockUserService) GetUsers(ctx context.Context, req *pb.GetUsersRequest) ([]models.User, int64, error) {
	args := m.Called(ctx, req)
	return args.Get(0).([]models.User), args.Get(1).(int64), args.Error(2)
}

func TestGRPCServer_GetUsers(t *testing.T) {
	ctx := context.Background()

	t.Run("InvalidSortDirection", func(t *testing.T) {
		req := &pb.GetUsersRequest{
			SortDirection: "invalid",
		}

		server := &GRPCServer{}

		_, err := server.GetUsers(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, codes.InvalidArgument, status.Code(err))
	})

	t.Run("ServiceError", func(t *testing.T) {
		req := &pb.GetUsersRequest{
			FirstName: "John",
		}

		mockService := new(MockUserService)
		mockService.On("GetUsers", ctx, req).Return([]models.User{}, int64(1), errors.New("service error"))

		server := &GRPCServer{Service: mockService}

		_, err := server.GetUsers(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, codes.Internal, status.Code(err))
	})

	t.Run("Success", func(t *testing.T) {
		req := &pb.GetUsersRequest{
			FirstName: "John",
		}

		mockService := new(MockUserService)
		users := []models.User{
			{
				ID:         uuid.New(),
				FirstName:  "John",
				SecondName: "Doe",
				Email:      "john.doe@example.com",
				CreatedAt:  time.Now(),
			},
		}
		mockService.On("GetUsers", ctx, req).Return(users, int64(1), nil)

		server := &GRPCServer{Service: mockService}

		response, err := server.GetUsers(ctx, req)
		assert.NoError(t, err)
		assert.Len(t, response.Users, 1)
		assert.Equal(t, "John", response.Users[0].FirstName)
		assert.Equal(t, int32(1), response.TotalMatchedCount)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		req := &pb.GetUsersRequest{
			FirstName: "John",
		}

		mockService := new(MockUserService)
		mockService.On("GetUsers", ctx, req).Return([]models.User{}, int64(0), nil)

		server := &GRPCServer{Service: mockService}

		response, err := server.GetUsers(ctx, req)
		assert.NoError(t, err)
		assert.Len(t, response.Users, 0)
	})
}
