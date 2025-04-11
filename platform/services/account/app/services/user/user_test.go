package user

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
)

type MockUserRepository struct {
	mock.Mock
}

func (m *MockUserRepository) FindUsers(ctx context.Context, req *repository.UserQuery) ([]models.User, int64, error) {
	args := m.Called(ctx, req)
	return args.Get(0).([]models.User), args.Get(1).(int64), args.Error(2)
}

func TestUserService_GetUsers(t *testing.T) {
	ctx := context.Background()

	t.Run("RepositoryError", func(t *testing.T) {
		query := repository.UserQuery{
			FirstName: "John",
		}
		req := &proto.GetUsersRequest{
			FirstName: "John",
		}

		mockRepo := new(MockUserRepository)
		mockRepo.On("FindUsers", ctx, &query).Return([]models.User{}, int64(0), errors.New("repository error"))

		service := NewuserService(mockRepo)

		_, _, err := service.GetUsers(ctx, req)
		assert.Error(t, err)
		assert.Equal(t, "repository error", err.Error())
	})

	t.Run("Success", func(t *testing.T) {
		query := repository.UserQuery{
			FirstName: "John",
		}
		req := &proto.GetUsersRequest{
			FirstName: "John",
		}

		mockRepo := new(MockUserRepository)
		users := []models.User{
			{
				ID:         uuid.New(),
				FirstName:  "John",
				SecondName: "Doe",
				Email:      "john.doe@example.com",
				CreatedAt:  time.Now(),
			},
		}
		mockRepo.On("FindUsers", ctx, &query).Return(users, int64(1), nil)

		service := NewuserService(mockRepo)

		response, totalMatchedCount, err := service.GetUsers(ctx, req)
		assert.NoError(t, err)
		assert.Equal(t, int64(1), totalMatchedCount)
		assert.Len(t, response, 1)
		assert.Equal(t, "John", response[0].FirstName)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		query := repository.UserQuery{
			FirstName: "John",
		}
		req := &proto.GetUsersRequest{
			FirstName: "John",
		}

		mockRepo := new(MockUserRepository)
		mockRepo.On("FindUsers", ctx, &query).Return([]models.User{}, int64(0), nil)

		service := NewuserService(mockRepo)

		response, totalMatchedCount, err := service.GetUsers(ctx, req)
		assert.NoError(t, err)
		assert.Equal(t, int64(0), totalMatchedCount)
		assert.Len(t, response, 0)
	})
}
