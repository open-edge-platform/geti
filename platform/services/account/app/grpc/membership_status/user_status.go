// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package user_status

import (
	"context"
	"errors"

	"account_service/app/common/utils"
	"account_service/app/config"
	"account_service/app/fsm"
	"account_service/app/grpc/common"
	grpcUtils "account_service/app/grpc/utils"
	"account_service/app/models"
	"account_service/app/roles"
	service "account_service/app/services/membership"

	"geti.com/account_service_grpc/pb"

	authzed "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/google/uuid"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
)

var logger = utils.InitializeLogger()

type GRPCServer struct {
	pb.UnimplementedUserStatusServer
	DB      *gorm.DB
	Service service.MembershipService
}

func (s *GRPCServer) Change(ctx context.Context, request *pb.UserStatusRequest) (*pb.UserStatusResponse, error) {
	logger.Debugf("user status change request - organization %s, user %s, new status: %s",
		request.OrganizationId, request.UserId, request.Status)

	userID, err := uuid.Parse(request.UserId)
	if err != nil {
		logger.Errorf("error parsing organization id: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid organization id")
	}

	orgID, err := uuid.Parse(request.OrganizationId)
	if err != nil {
		logger.Errorf("error parsing organization id: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid organization id")
	}

	newUserStatus := models.UserStatus{}

	transaction := func(tx *gorm.DB) error {
		oldCurrentUserStatus := models.UserStatus{}
		dbResult := tx.First(&oldCurrentUserStatus, "user_id = ? AND organization_id = ? AND current = ?", userID.String(), orgID.String(), "TRUE")
		if dbResult.Error != nil {
			logger.Errorf("error during getting user status: %v", dbResult.Error)
			if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
				return status.Errorf(codes.NotFound, "User status not found for user ID: \"%v\" and organization ID: \"%v\"", userID.String(), orgID.String())
			}
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		err := fsm.UserStatusFSM.Transition(oldCurrentUserStatus.Status, request.Status)
		if err != nil {
			logger.Errorf("error validating user status transition: %v", err)
			return status.Errorf(codes.FailedPrecondition, "incorrect status")
		}

		if request.Status == "DEL" {
			err = common.CheckIfLastRegisteredOrgAdmin(s.DB, orgID.String(), userID.String())
			if err != nil {
				return err
			}
		}

		oldCurrentUserStatus.Current = false

		dbResult = tx.Save(&oldCurrentUserStatus)
		if dbResult.Error != nil {
			logger.Errorf("error during user status update: %v", dbResult.Error)
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		if request.Status == "DEL" {
			pat := models.PersonalAccessToken{}
			patDbResult := s.DB.Model(&pat).Where("status = ? AND user_id = ? AND organization_id = ?", "ACT", userID.String(), orgID.String()).Update("status", "DEL")
			if patDbResult.Error != nil {
				logger.Errorf("error during personal access token update: %v", patDbResult.Error)
				return status.Errorf(codes.Unauthenticated, "Unexpected error")
			}

			rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
			if err != nil {
				logger.Errorf("unable to initialize roles manager: %v", err)
				return status.Errorf(codes.Unknown, "unexpected error")
			}

			userRelationships, err := rolesMgr.GetUserAllRelationships(userID.String())
			if err != nil {
				logger.Errorf("unable to get all user relationships: %v", err)
				return status.Errorf(codes.Unknown, "unexpected error")
			}

			for _, relationship := range userRelationships {
				deleteRelation, err := rolesMgr.CheckRelationshipToDelete(relationship, orgID.String())
				if err != nil {
					logger.Errorf("failed to determine if relationship should be deleted: %v", err)
					return status.Errorf(codes.Unknown, "unexpected error")
				}
				if deleteRelation {
					err := rolesMgr.ChangeUserRelation(relationship.Resource.ObjectType, relationship.Resource.ObjectId, []string{relationship.Relation}, userID.String(), authzed.RelationshipUpdate_OPERATION_DELETE)
					if err != nil {
						logger.Errorf("failed to delete user relationship: %v", err)
						return status.Errorf(codes.Unknown, "unexpected error")
					}
				}
			}
		}

		newUserStatus = models.UserStatus{
			Status:         request.Status,
			OrganizationID: orgID,
			UserID:         userID,
			Current:        true,
			CreatedBy:      request.CreatedBy,
		}

		authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if ok {
			newUserStatus.CreatedBy = authTokenData.UserID
		}

		dbResult = tx.Create(&newUserStatus)
		if dbResult.Error != nil {
			logger.Errorf("error during user status Create: %v", dbResult.Error)
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		return nil
	}

	err = s.DB.Transaction(transaction)
	if err != nil {
		return nil, err
	}

	response := pb.UserStatusResponse{
		Id:             newUserStatus.ID.String(),
		Status:         newUserStatus.Status,
		OrganizationId: newUserStatus.OrganizationID.String(),
		UserId:         newUserStatus.UserID.String(),
		CreatedBy:      newUserStatus.CreatedBy,
		CreatedAt:      timestamppb.New(newUserStatus.CreatedAt),
	}

	return &response, nil

}
