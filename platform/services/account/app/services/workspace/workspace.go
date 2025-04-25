// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package workspace

import (
	"account_service/app/common/utils"
	"account_service/app/models"
	"errors"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"gorm.io/gorm"
)

type Service struct {
	DB *gorm.DB
}

var logger = utils.InitializeLogger()

func (s *Service) GetDefaultWorkspace(orgId string) (*models.Workspace, error) {
	var defaultWorkspace models.Workspace
	dbResult := s.DB.Where("organization_id = ?", orgId).First(&defaultWorkspace)
	if dbResult.Error != nil {
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			logger.Errorf("Default workspace not found for organization ID: %s", orgId)
			return nil, status.Error(codes.NotFound, "default workspace not found")
		}
		logger.Errorf("Error retrieving default workspace: %v", dbResult.Error)
		return nil, status.Error(codes.Internal, "unexpected error")
	}
	return &defaultWorkspace, nil
}
