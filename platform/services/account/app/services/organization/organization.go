// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package organization

import (
	"context"
	"errors"
	"fmt"

	accErr "account_service/app/errors"
	"account_service/app/models"
	"account_service/app/repository"
	"account_service/app/services"
	roleService "account_service/app/services/role"
	"common/utils"

	"gorm.io/gorm"
)

var logger = utils.InitializeLogger()

type Service struct {
	DB *gorm.DB
}

func CreateOrganizationWithStatusHistory(tx *gorm.DB, org *models.Organization) error {
	orgStatusHistoryEntry := models.OrganizationStatusHistory{
		Status: org.Status,
	}

	err := org.Create(tx)
	if err != nil {
		logger.Errorf("error during organization Create: %v", err.Error())
		var aerr *models.AlreadyExistsError
		ok := errors.As(err, &aerr)
		if ok {
			return services.NewAlreadyExistsError(aerr.Error())
		}
		return err
	}

	orgStatusHistoryEntry.OrganizationID = org.ID

	err = orgStatusHistoryEntry.Create(tx)
	if err != nil {
		logger.Errorf("error during organization status history Create: %v", err.Error())
		return err
	}

	logger.Infof("Organization '%s' with ID %s has been successfully created, status: %s",
		org.Name, org.ID.String(), org.Status)
	return nil
}

func (s *Service) CreateOrganization(org *models.Organization) error {
	transaction := func(tx *gorm.DB) error {
		return CreateOrganizationWithStatusHistory(tx, org)
	}

	err := s.DB.Transaction(transaction)
	if err != nil {
		logger.Errorf("failed to create the organization named %s: %v", org.Name, err)
		return err
	}
	return nil
}

type OrganizationService interface {
	CheckIfLastRegisteredOrgAdmin(ctx context.Context, orgId string, userId string) error
}

type organizationService struct {
	repo        repository.OrganizationRepository
	RoleService roleService.IRoleService
}

func NewOrganizationRepository(repo repository.OrganizationRepository, roleService roleService.IRoleService) OrganizationService {
	return &organizationService{repo: repo, RoleService: roleService}
}

func (r *organizationService) CheckIfLastRegisteredOrgAdmin(ctx context.Context, orgId string, userId string) error {
	isLastOrgAdmin, err := r.RoleService.IsLastOrgAdmin(orgId, userId)
	if err != nil {
		logger.Errorf("Error checking if user is last org admin: %v", err)
		return accErr.NewUnknownError("unexpected error")
	}

	if isLastOrgAdmin {
		org, err := r.repo.GetOrg(ctx, orgId)
		if err != nil {
			if errors.Is(err, gorm.ErrRecordNotFound) {
				return accErr.NewNotFoundError(fmt.Sprintf("organization ID: \"%v\" not found", orgId))
			}
			return accErr.NewUnknownError("unexpected error")
		}

		if org.Status != "RGS" && org.Status != "REQ" {
			return accErr.NewConflictError("You cannot remove the last admin in the organization.")
		}
	}
	return nil
}
