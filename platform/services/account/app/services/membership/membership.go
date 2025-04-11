// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package membership

import (
	"context"

	accErr "account_service/app/errors"
	"account_service/app/fsm"
	"account_service/app/models"
	"account_service/app/repository"
	orgService "account_service/app/services/organization"
	roleService "account_service/app/services/role"
	"common/utils"

	proto "geti.com/account_service_grpc/pb"

	"github.com/google/uuid"
	"google.golang.org/protobuf/types/known/emptypb"
)

var logger = utils.InitializeLogger()

type MembershipService interface {
	GetMemberships(ctx context.Context, req *proto.MembershipRequest) ([]models.MembershipResult, int64, error)
	DeleteMemberships(ctx context.Context, req *proto.DeleteMembershipRequest) (*emptypb.Empty, error)
	SetUserStatus(ctx context.Context, userID uuid.UUID, organizationID uuid.UUID, status string) (*models.UserStatus, error)
	GetUserMemberships(ctx context.Context, req *proto.UserMembershipRequest) ([]models.UserMembershipResult, int64, error)
}

type membershipService struct {
	repo                repository.MembershipRepository
	patRepo             repository.PersonalAccessTokenRepository
	OrganizationService orgService.OrganizationService
	RoleService         roleService.IRoleService
}

func NewMembershipService(
	repo repository.MembershipRepository,
	patRepo repository.PersonalAccessTokenRepository,
	orgService orgService.OrganizationService,
	roleService roleService.IRoleService) MembershipService {
	return &membershipService{
		repo:                repo,
		patRepo:             patRepo,
		OrganizationService: orgService,
		RoleService:         roleService}
}

func (s *membershipService) GetMemberships(ctx context.Context, req *proto.MembershipRequest) ([]models.MembershipResult, int64, error) {
	dataQuery := repository.MembershipQuery{FirstName: req.FirstName, SecondName: req.SecondName, Email: req.Email, Status: req.Status, CreatedAt: req.CreatedAt, Name: req.Name, OrganizationId: req.OrganizationId, SortBy: req.SortBy, SortDirection: req.SortDirection, Skip: req.Skip, Limit: req.Limit}
	memberships, totalMatchedCount, err := s.repo.FindMemberships(ctx, &dataQuery)
	if err != nil {
		return nil, 0, err
	}

	return memberships, totalMatchedCount, nil
}

func (s *membershipService) DeleteMemberships(ctx context.Context, req *proto.DeleteMembershipRequest) (*emptypb.Empty, error) {
	membershipResult, err := s.repo.DeleteMemberships(ctx, req.UserId, req.OrganizationId, s.patRepo)

	if err != nil {
		logger.Errorf("Delete membership Error %v", err)
		return nil, err
	}

	return membershipResult, nil
}

func (s *membershipService) SetUserStatus(ctx context.Context, userID uuid.UUID, organizationID uuid.UUID, status string) (*models.UserStatus, error) {
	dataQuery := repository.UserMembershipQuery{
		UserId:         userID.String(),
		OrganizationId: organizationID.String(),
	}
	oldUserStatus, _, err := s.repo.FindUserMemberships(ctx, &dataQuery)
	if err != nil {
		logger.Errorf("error during getting user status: %v", err)
		return nil, accErr.NewUnknownError("unexpected error")
	}

	fsmerr := fsm.UserStatusFSM.Transition(oldUserStatus[0].Status, status)
	if fsmerr != nil {
		logger.Errorf("error validating user status transition: %v", fsmerr)
		return nil, accErr.NewConflictError("incorrect status")
	}
	if status == "DEL" {
		err = s.OrganizationService.CheckIfLastRegisteredOrgAdmin(ctx, organizationID.String(), userID.String())
		if err != nil {
			return nil, err
		}
	}

	oldUserStatus[0].Current = false

	err = s.repo.SaveUserMembership(ctx, &oldUserStatus[0])
	if err != nil {
		logger.Errorf("error during user status update: %v", err)
		return nil, accErr.NewUnknownError("unexpected error")
	}

	if status == "DEL" {
		err = s.repo.UpdatePersonalAccessTokenMembership(ctx, userID.String(), organizationID.String(), "DEL")
		if err != nil {
			logger.Errorf("error during personal access token update: %v", err)
			return nil, accErr.NewUnauthenticatedError("unexpected error")
		}

		err := s.RoleService.DeleteUserRelations(organizationID.String(), userID.String())
		if err != nil {
			return nil, accErr.NewInternalError("unexpected error")
		}

	}
	newUserStatus := models.UserStatus{
		Status:         status,
		OrganizationID: organizationID,
		UserID:         userID,
		Current:        true,
	}
	err = s.repo.SaveUserMembership(ctx, &newUserStatus)
	if err != nil {
		logger.Errorf("error during user status Create: %v", err)
		return nil, accErr.NewUnknownError("unexpected error")
	}

	return &newUserStatus, nil
}

func (s *membershipService) GetUserMemberships(ctx context.Context, req *proto.UserMembershipRequest) ([]models.UserMembershipResult, int64, error) {
	dataQuery := repository.UserMembershipQuery{
		UserId:           req.UserId,
		OrganizationName: req.OrganizationName,
		SortBy:           req.SortBy,
		SortDirection:    req.SortDirection,
		Skip:             req.Skip,
		Limit:            req.Limit,
	}
	userStatuses, totalMatchedCount, err := s.repo.FindUserMemberships(ctx, &dataQuery)
	if err != nil {
		return nil, 0, err
	}

	var userMembershipResults []models.UserMembershipResult
	for _, userStatus := range userStatuses {
		userMembershipResults = append(userMembershipResults, models.UserMembershipResult{
			ID:               userStatus.ID,
			OrganizationID:   userStatus.OrganizationID,
			OrganizationName: userStatus.OrganizationName,
			Status:           userStatus.Status,
			CreatedAt:        userStatus.CreatedAt,
		})
	}

	return userMembershipResults, totalMatchedCount, nil
}
