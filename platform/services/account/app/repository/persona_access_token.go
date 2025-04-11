// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package repository

import (
	accErr "account_service/app/errors"
	"account_service/app/models"

	"gorm.io/gorm"
)

type PersonalAccessTokenRepository interface {
	DeactivatePersonalAccessTokens(userID string, organizationID string) error
}

type personalAccessTokenRepository struct {
	db *gorm.DB
}

func NewPersonalAccessTokenRepository(db *gorm.DB) PersonalAccessTokenRepository {
	return &personalAccessTokenRepository{db: db}
}

func (r *personalAccessTokenRepository) DeactivatePersonalAccessTokens(userID string, organizationID string) error {
	pat := models.PersonalAccessToken{}
	patDbResult := r.db.Model(&pat).Where("status = ? AND user_id = ? AND organization_id = ?", "ACT", userID, organizationID).Update("status", "DEL")
	if patDbResult.Error != nil {
		return accErr.NewUnknownError("unexpected error during pat update")
	}
	return nil
}
