// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package repository

import (
	"context"

	"account_service/app/models"

	"gorm.io/gorm"
)

type OrganizationRepository interface {
	GetOrg(ctx context.Context, orgId string) (models.Organization, error)
}

type organizationRepository struct {
	db *gorm.DB
}

func NewOrganizationRepository(db *gorm.DB) OrganizationRepository {
	return &organizationRepository{db: db}
}

func (r *organizationRepository) GetOrg(ctx context.Context, orgId string) (models.Organization, error) {
	org := models.Organization{}
	dbResult := r.db.WithContext(ctx).
		Model(&org).
		First(&org, "id = ?", orgId)
	if dbResult.Error != nil {
		return models.Organization{}, dbResult.Error
	}
	return org, nil
}
