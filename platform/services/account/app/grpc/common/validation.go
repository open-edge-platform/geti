// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package common

import (
	"errors"

	"account_service/app/config"
	"account_service/app/models"
	"account_service/app/roles"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"gorm.io/gorm"
)

func IsLastOrgAdmin(orgID string, userID string) (bool, error) {
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize client: %v", err)
		return false, err
	}

	adminsRelationships, err := rolesMgr.GetOrganizationRelationships(orgID, "organization_admin")
	if err != nil {
		logger.Errorf("error during getting organization admin relationships: %v", err)
		return false, err
	}

	return len(adminsRelationships) == 1 && adminsRelationships[0].Subject.Object.ObjectId == userID, nil
}

func CheckIfLastRegisteredOrgAdmin(db *gorm.DB, orgId string, userId string) error {
	isLastOrgAdmin, err := IsLastOrgAdmin(orgId, userId)
	if err != nil {
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	if isLastOrgAdmin {
		org := models.Organization{}
		dbResult := db.First(&org, "id = ?", orgId)
		if dbResult.Error != nil {
			logger.Errorf("error during getting organization: %v", dbResult.Error)
			if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
				return status.Errorf(codes.NotFound, "organization ID: \"%v\" not found", orgId)
			}
			return status.Errorf(codes.Unknown, "unexpected error")
		}
		if org.Status != "RGS" {
			return status.Error(codes.FailedPrecondition,
				"You cannot remove the last admin in the organization.")
		}
	}
	return nil
}
