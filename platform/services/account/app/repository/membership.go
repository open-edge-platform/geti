// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package repository

import (
	"account_service/app/config"
	accErr "account_service/app/errors"
	"account_service/app/grpc/common"
	"account_service/app/models"
	"account_service/app/roles"
	"context"
	"errors"

	authzed "github.com/authzed/authzed-go/proto/authzed/api/v1"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
)

type MembershipQuery struct {
	FirstName      string
	SecondName     string
	Email          string
	Status         string
	CreatedAt      *timestamppb.Timestamp
	Name           string
	OrganizationId string
	SortBy         string
	SortDirection  string
	Skip           int32
	Limit          int32
}

type UserMembershipQuery struct {
	UserId           string
	OrganizationId   string
	OrganizationName string
	SortBy           string
	SortDirection    string
	Skip             int32
	Limit            int32
}

type MembershipRepository interface {
	FindMemberships(ctx context.Context, req *MembershipQuery) ([]models.MembershipResult, int64, error)
	SaveUserMembership(ctx context.Context, userStatus *models.UserStatus) error
	UpdatePersonalAccessTokenMembership(ctx context.Context, userID string, organizationID string, newStatus string) error
	FindUserMemberships(ctx context.Context, req *UserMembershipQuery) ([]models.UserStatus, int64, error)
	DeleteMemberships(ctx context.Context, userID string, organizationID string, patRepo PersonalAccessTokenRepository) (*emptypb.Empty, error)
	FindMembershipsToDelete(ctx context.Context, userID string, organizationID string) (*[]models.UserStatus, error)
}

type membershipRepository struct {
	db *gorm.DB
}

func NewMembershipRepository(db *gorm.DB) MembershipRepository {
	return &membershipRepository{db: db}
}

func (r *membershipRepository) FindMemberships(ctx context.Context, req *MembershipQuery) ([]models.MembershipResult, int64, error) {
	var memberships []models.MembershipResult

	statementSession := r.db.WithContext(ctx).
		Model(&models.UserStatus{}).
		Joins("JOIN users ON users.id = user_statuses.user_id").
		Where("user_statuses.organization_id = ? AND user_statuses.current = true", req.OrganizationId).
		Select("user_statuses.id, user_statuses.user_id, users.first_name, users.second_name, users.email, user_statuses.status, user_statuses.created_at")

	if req.FirstName != "" {
		statementSession = statementSession.Where("LOWER(users.first_name) = LOWER(?)", req.FirstName)
	}
	if req.SecondName != "" {
		statementSession = statementSession.Where("LOWER(users.second_name) = LOWER(?)", req.SecondName)
	}
	if req.Email != "" {
		statementSession = statementSession.Where("LOWER(users.email) = LOWER(?)", req.Email)
	}
	if req.Status != "" {
		statementSession = statementSession.Where("user_statuses.status = ?", req.Status)
	}
	if req.Name != "" {
		statementSession = statementSession.Where(
			"LOWER(users.first_name) LIKE LOWER(?) OR LOWER(users.second_name) LIKE LOWER(?) OR LOWER(users.email) LIKE LOWER(?)",
			"%"+req.Name+"%", "%"+req.Name+"%", "%"+req.Name+"%",
		)
	}
	if req.SortBy != "" && req.SortDirection != "" {
		orderQuery, err := common.CreateOrderQuery(models.UserStatus{}, req.SortBy, req.SortDirection)
		if err != nil {
			return nil, 0, err
		}
		statementSession = statementSession.Order(orderQuery)
	}

	var totalMatchedCount int64
	dbResult := statementSession.Count(&totalMatchedCount)
	if dbResult.Error != nil {
		return nil, 0, dbResult.Error
	}

	if req.Skip > 0 {
		statementSession = statementSession.Offset(int(req.Skip))
	}
	if req.Limit > 0 {
		statementSession = statementSession.Limit(int(req.Limit))
	}

	dbResult = statementSession.Find(&memberships)
	if dbResult.Error != nil {
		return nil, 0, dbResult.Error
	}

	return memberships, totalMatchedCount, nil
}

func (r *membershipRepository) SaveUserMembership(ctx context.Context, userStatus *models.UserStatus) error {
	err := r.db.WithContext(ctx).Save(userStatus).Error
	if err != nil {
		return err
	}
	return nil
}

func (r *membershipRepository) UpdatePersonalAccessTokenMembership(ctx context.Context, userID string, organizationID string, newStatus string) error {
	pat := models.PersonalAccessToken{}
	patDbResult := r.db.WithContext(ctx).
		Model(&pat).
		Where("status = ? AND user_id = ? AND organization_id = ?", "ACT", userID, organizationID).
		Update("status", newStatus)
	if patDbResult.Error != nil {
		return patDbResult.Error
	}
	return nil
}

func (r *membershipRepository) FindUserMemberships(ctx context.Context, req *UserMembershipQuery) ([]models.UserStatus, int64, error) {
	var userStatuses []models.UserStatus

	statementSession := r.db.WithContext(ctx).
		Model(&models.UserStatus{}).
		Joins("JOIN organizations ON user_statuses.organization_id = organizations.id").
		Where("user_statuses.current = true").
		Select("user_statuses.id, user_statuses.user_id, user_statuses.organization_id, organizations.name AS organization_name, user_statuses.status, user_statuses.created_at")

	if req.UserId != "" {
		statementSession = statementSession.Where("user_id = ?", req.UserId)
	}
	if req.OrganizationId != "" {
		statementSession = statementSession.Where("organization_id = ?", req.OrganizationId)
	}
	if req.OrganizationName != "" {
		statementSession = statementSession.Where("LOWER(organizations.name) LIKE LOWER(?)", "%"+req.OrganizationName+"%")
	}
	if req.SortBy != "" && req.SortDirection != "" {
		orderQuery, err := common.CreateOrderQuery(models.UserStatus{}, req.SortBy, req.SortDirection)
		if err != nil {
			return nil, 0, err
		}
		statementSession = statementSession.Order(orderQuery)
	}

	var totalMatchedCount int64
	dbResult := statementSession.Count(&totalMatchedCount)
	if dbResult.Error != nil {
		return nil, 0, dbResult.Error
	}

	if req.Skip > 0 {
		statementSession = statementSession.Offset(int(req.Skip))
	}
	if req.Limit > 0 {
		statementSession = statementSession.Limit(int(req.Limit))
	}

	dbResult = statementSession.Find(&userStatuses)
	if dbResult.Error != nil {
		return nil, 0, dbResult.Error
	}

	return userStatuses, totalMatchedCount, nil
}

func (r *membershipRepository) FindMembershipsToDelete(ctx context.Context, userID string, organizationID string) (*[]models.UserStatus, error) {
	memberships := []models.UserStatus{}
	membershipsResult := r.db.WithContext(ctx).
		Model(&memberships).Where("user_id = ? AND organization_id = ?", userID, organizationID)

	if membershipsResult.Error != nil {
		if errors.Is(membershipsResult.Error, gorm.ErrRecordNotFound) {
			return nil, accErr.NewNotFoundError("Membership not found")
		}
		return nil, accErr.NewUnknownError("unexpected error during getting memberships to delete")
	}

	membershipsResult.Find(&memberships)
	return &memberships, nil
}

func (r *membershipRepository) DeleteMemberships(ctx context.Context, userID string, organizationID string, patRepo PersonalAccessTokenRepository) (*emptypb.Empty, error) {
	transaction := func(tx *gorm.DB) error {
		memberships, err := r.FindMembershipsToDelete(ctx, userID, organizationID)
		if err != nil {
			return err
		}

		for _, membership := range *memberships {

			err := common.CheckIfLastRegisteredOrgAdmin(r.db, organizationID, userID)
			if err != nil {
				return accErr.NewUnknownError(err.Error())
			}

			patErr := patRepo.DeactivatePersonalAccessTokens(userID, organizationID)
			if patErr != nil {
				return patErr
			}

			rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
			if err != nil {
				return accErr.NewUnknownError("unexpected error during role manager initialization")
			}

			userRelationships, err := rolesMgr.GetUserAllRelationshipsByOrganization(membership.OrganizationID.String(), membership.UserID.String())
			if err != nil {
				return accErr.NewUnknownError("unexpected error during getting user relations")
			}

			for _, relationship := range userRelationships {
				deleteRelation, err := rolesMgr.CheckRelationshipToDelete(relationship, membership.OrganizationID.String())
				if err != nil {
					return status.Errorf(codes.Unknown, "unexpected error")
				}
				if deleteRelation {
					err := rolesMgr.ChangeUserRelation(relationship.Resource.ObjectType, relationship.Resource.ObjectId, []string{relationship.Relation}, membership.UserID.String(), authzed.RelationshipUpdate_OPERATION_DELETE)
					if err != nil {
						return accErr.NewUnknownError("unexpected error during deleting user relation")
					}
				}
			}

			dbErr := r.db.Delete(&membership)
			if dbErr.Error != nil {
				return accErr.NewUnknownError("unexpected error during deleting membership")
			}

			if dbErr.RowsAffected == 0 {
				return accErr.NewNotFoundError("No user found to delete")
			}

		}
		return nil
	}

	err := r.db.Transaction(transaction)
	if err != nil {
		return nil, err
	}

	return &emptypb.Empty{}, nil
}
