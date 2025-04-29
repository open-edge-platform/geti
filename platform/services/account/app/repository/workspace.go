// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package repository

import (
	"account_service/app/common/utils"
	accErr "account_service/app/errors"
	"account_service/app/grpc/common"
	"account_service/app/models"

	"context"
	"fmt"

	"gorm.io/gorm"
)

var logger = utils.InitializeLogger()

type WorkspaceRepository interface {
	FindWorkspaces(ctx context.Context, findRequest models.FindWorkspaceRequest) ([]models.Workspace, int32, error)
}

type workspaceRepository struct {
	db *gorm.DB
}

func NewWorkspaceRepository(db *gorm.DB) WorkspaceRepository {
	return &workspaceRepository{db: db}
}

func (r *workspaceRepository) FindWorkspaces(ctx context.Context, findRequest models.FindWorkspaceRequest) ([]models.Workspace, int32, error) {
	logger.Debugf("find workspace request: %v", findRequest)

	var workspaces []models.Workspace
	statementSession := r.db.WithContext(ctx)
	statementSession = statementSession.Model(&workspaces)

	if findRequest.Name != "" {
		statementSession = statementSession.Where("name LIKE ?", fmt.Sprintf("%%%s%%", findRequest.Name))
	}
	if findRequest.OrganizationId != "" {
		statementSession = statementSession.Where("organization_id = ?", findRequest.OrganizationId)
	}
	if findRequest.BillingChildAccountId != "" {
		statementSession = statementSession.Where("billing_child_account_id = ?", findRequest.BillingChildAccountId)
	}

	if findRequest.CreatedAtFrom != nil && findRequest.CreatedAtTo != nil {
		statementSession = statementSession.Where(
			"created_at BETWEEN ? AND ?", findRequest.CreatedAtFrom, findRequest.CreatedAtTo,
		)
	} else if findRequest.CreatedAtFrom != nil {
		statementSession = statementSession.Where("created_at > ?", findRequest.CreatedAtFrom)
	} else if findRequest.CreatedAtTo != nil {
		statementSession = statementSession.Where("created_at < ?", findRequest.CreatedAtTo)
	}
	if findRequest.CreatedBy != "" {
		statementSession = statementSession.Where("created_by = ?", findRequest.CreatedBy)
	}

	if findRequest.ModifiedAtFrom != nil && findRequest.ModifiedAtTo != nil {
		statementSession = statementSession.Where(
			"modified_at BETWEEN ? AND ?", findRequest.ModifiedAtFrom, findRequest.ModifiedAtTo,
		)
	} else if findRequest.ModifiedAtFrom != nil {
		statementSession = statementSession.Where("modified_at > ?", findRequest.ModifiedAtFrom)
	} else if findRequest.ModifiedAtTo != nil {
		statementSession = statementSession.Where("modified_at < ?", findRequest.ModifiedAtTo)
	}
	if findRequest.ModifiedBy != "" {
		statementSession = statementSession.Where("modified_by = ?", findRequest.ModifiedBy)
	}

	if findRequest.SortBy != "" && findRequest.SortDirection != "" {
		orderQuery, err := common.CreateOrderQuery(models.Workspace{}, findRequest.SortBy, findRequest.SortDirection)
		if err != nil {
			return nil, 0, err
		}
		statementSession = statementSession.Order(orderQuery)
	}

	var totalMatchedCount int64
	dbResult := statementSession.Count(&totalMatchedCount)
	if dbResult.Error != nil {
		logger.Errorf("error during workspace count: %v", dbResult.Error)
		return nil, 0, accErr.NewDatabaseError("unexpected error", "0")
	}

	if findRequest.Skip > 0 {
		statementSession = statementSession.Offset(int(findRequest.Skip))
	}

	if findRequest.Limit > 0 {
		statementSession = statementSession.Limit(int(findRequest.Limit))
	}

	dbResult = statementSession.Find(&workspaces)
	if dbResult.Error != nil {
		logger.Errorf("error during workspace find: %v", dbResult.Error)
		return nil, 0, accErr.NewDatabaseError("unexpected error", "0")
	}

	return workspaces, int32(totalMatchedCount), nil
}
