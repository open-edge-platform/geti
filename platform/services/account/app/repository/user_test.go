package repository_test

import (
	"account_service/app/repository"
	"context"
	"errors"
	"regexp"
	"testing"
	"time"

	"gopkg.in/DATA-DOG/go-sqlmock.v1"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func setupMockDB(t *testing.T) (*gorm.DB, sqlmock.Sqlmock) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to open sqlmock database: %v", err)
	}

	dialector := postgres.New(postgres.Config{
		Conn: db,
	})
	gormDB, err := gorm.Open(dialector, &gorm.Config{})
	if err != nil {
		t.Fatalf("failed to open gorm database: %v", err)
	}

	return gormDB, mock
}

func TestFindUsers(t *testing.T) {
	ctx := context.Background()

	t.Run("RepositoryError", func(t *testing.T) {
		gormDB, mock := setupMockDB(t)
		defer mock.ExpectClose()

		query := &repository.UserQuery{
			FirstName: "John",
		}

		mock.ExpectQuery(regexp.QuoteMeta(`SELECT count(*) FROM "users" WHERE LOWER(first_name) = LOWER($1)`)).
			WithArgs("John").
			WillReturnError(errors.New("repository error"))

		repo := repository.NewUserRepository(gormDB)

		users, totalMatchedCount, err := repo.FindUsers(ctx, query)
		assert.Error(t, err)
		assert.Equal(t, int64(0), totalMatchedCount)
		assert.Len(t, users, 0)
	})

	t.Run("Success", func(t *testing.T) {
		gormDB, mock := setupMockDB(t)
		defer mock.ExpectClose()

		query := &repository.UserQuery{
			FirstName: "John",
		}

		mock.ExpectQuery(regexp.QuoteMeta(`SELECT count(*) FROM "users" WHERE LOWER(first_name) = LOWER($1)`)).
			WithArgs("John").
			WillReturnRows(sqlmock.NewRows([]string{"count"}).AddRow(1))

		mock.ExpectQuery(regexp.QuoteMeta(`SELECT * FROM "users" WHERE LOWER(first_name) = LOWER($1)`)).
			WithArgs("John").
			WillReturnRows(sqlmock.NewRows([]string{"id", "first_name", "second_name", "email", "created_at"}).
				AddRow(uuid.New().String(), "John", "Doe", "john.doe@example.com", time.Now()))

		repo := repository.NewUserRepository(gormDB)

		users, totalMatchedCount, err := repo.FindUsers(ctx, query)
		assert.NoError(t, err)
		assert.Equal(t, int64(1), totalMatchedCount)
		assert.Len(t, users, 1)
		assert.Equal(t, "John", users[0].FirstName)
	})

	t.Run("EmptyResult", func(t *testing.T) {
		gormDB, mock := setupMockDB(t)
		defer mock.ExpectClose()

		query := &repository.UserQuery{
			FirstName: "John",
		}

		mock.ExpectQuery(regexp.QuoteMeta(`SELECT count(*) FROM "users" WHERE LOWER(first_name) = LOWER($1)`)).
			WithArgs("John").
			WillReturnRows(sqlmock.NewRows([]string{"count"}).AddRow(0))

		repo := repository.NewUserRepository(gormDB)

		users, totalMatchedCount, err := repo.FindUsers(ctx, query)
		assert.Error(t, err)
		assert.Equal(t, int64(0), totalMatchedCount)
		assert.Len(t, users, 0)
	})
}
