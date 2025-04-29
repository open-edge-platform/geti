// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package repository

import (
	accErr "account_service/app/errors"
	"account_service/app/grpc/common"
	"account_service/app/models"
	"context"

	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
)

type UserQuery struct {
	FirstName              string
	SecondName             string
	Email                  string
	ExternalId             string
	Country                string
	LastSuccessfulLogin    *timestamppb.Timestamp
	CurrentSuccessfulLogin *timestamppb.Timestamp
	CreatedFrom            *timestamppb.Timestamp
	CreatedTo              *timestamppb.Timestamp
	ModifiedFrom           *timestamppb.Timestamp
	ModifiedTo             *timestamppb.Timestamp
	UserConsentFrom        *timestamppb.Timestamp
	UserConsentTo          *timestamppb.Timestamp
	Name                   string
	SortBy                 string
	SortDirection          string
	Skip                   int32
	Limit                  int32
}

type userRepository struct {
	db *gorm.DB
}

type UserRepository interface {
	FindUsers(ctx context.Context, req *UserQuery) ([]models.User, int64, error)
}

func NewUserRepository(db *gorm.DB) UserRepository {
	return &userRepository{db: db}
}

func (r *userRepository) FindUsers(ctx context.Context, req *UserQuery) ([]models.User, int64, error) {
	var Users []models.User

	statementSession := r.db.WithContext(ctx).
		Model(&models.User{})

	if req.FirstName != "" {
		statementSession = statementSession.Where("LOWER(first_name) = LOWER(?)", req.FirstName)
	}
	if req.SecondName != "" {
		statementSession = statementSession.Where("LOWER(second_name) = LOWER(?)", req.SecondName)
	}
	if req.Email != "" {
		statementSession = statementSession.Where("LOWER(email) = LOWER(?)", req.Email)
	}
	if req.ExternalId != "" {
		statementSession = statementSession.Where("LOWER(external_id) = LOWER(?)", req.ExternalId)
	}
	if req.Country != "" {
		statementSession = statementSession.Where("LOWER(country) = LOWER(?)", req.Country)
	}
	if req.LastSuccessfulLogin != nil {
		statementSession = statementSession.Where("last_successful_login = ?", req.LastSuccessfulLogin.AsTime())
	}
	if req.CurrentSuccessfulLogin != nil {
		statementSession = statementSession.Where("current_successful_login = ?", req.CurrentSuccessfulLogin.AsTime())
	}
	if req.CreatedFrom != nil && req.CreatedTo != nil {
		statementSession = statementSession.Where(
			"created_at BETWEEN ? AND ?", req.CreatedFrom.AsTime(), req.CreatedTo.AsTime(),
		)
	} else if req.CreatedFrom != nil {
		statementSession = statementSession.Where("created_at > ?", req.CreatedFrom.AsTime())
	} else if req.CreatedTo != nil {
		statementSession = statementSession.Where("created_at < ?", req.CreatedTo.AsTime())
	}
	if req.ModifiedFrom != nil && req.ModifiedTo != nil {
		statementSession = statementSession.Where(
			"modified_at BETWEEN ? AND ?", req.ModifiedFrom.AsTime(), req.ModifiedTo.AsTime(),
		)
	} else if req.ModifiedFrom != nil {
		statementSession = statementSession.Where("modified_at > ?", req.ModifiedFrom.AsTime())
	} else if req.ModifiedTo != nil {
		statementSession = statementSession.Where("modified_at < ?", req.ModifiedTo.AsTime())
	}
	if req.UserConsentFrom != nil && req.UserConsentTo != nil {
		statementSession = statementSession.Where(
			"user_consent_at BETWEEN ? AND ?", req.UserConsentFrom.AsTime(), req.UserConsentTo.AsTime(),
		)
	} else if req.UserConsentFrom != nil {
		statementSession = statementSession.Where("user_consent_at > ?", req.UserConsentFrom.AsTime())
	} else if req.UserConsentTo != nil {
		statementSession = statementSession.Where("user_consent_at < ?", req.UserConsentTo.AsTime())
	}
	if req.Name != "" {
		statementSession = statementSession.Where(
			"LOWER(first_name) LIKE LOWER(?) OR LOWER(second_name) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?)",
			"%"+req.Name+"%", "%"+req.Name+"%", "%"+req.Name+"%",
		)
	}
	if req.SortBy != "" && req.SortDirection != "" {
		orderQuery, err := common.CreateOrderQuery(models.UserStatus{}, req.SortBy, req.SortDirection)
		if err != nil {
			return nil, 0, err
		}
		statementSession = statementSession.Order(orderQuery).Order("id")
	}

	var totalMatchedCount int64
	dbResult := statementSession.Count(&totalMatchedCount)
	if dbResult.Error != nil {
		return nil, 0, accErr.NewUnknownError("failed to count users")
	}
	if req.Skip > 0 {
		statementSession = statementSession.Offset(int(req.Skip))
	}
	if req.Limit > 0 {
		statementSession = statementSession.Limit(int(req.Limit))
	}
	if totalMatchedCount == 0 {
		return nil, totalMatchedCount, accErr.NewNotFoundError("Users not found")
	}

	dbResult = statementSession.Find(&Users)
	if dbResult.Error != nil {
		return nil, 0, accErr.NewUnknownError("failed to find users")
	}

	return Users, totalMatchedCount, nil
}
