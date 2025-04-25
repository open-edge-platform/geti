// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package organization_status

import (
	"context"
	"errors"
	"fmt"
	"strconv"

	"account_service/app/common/utils"
	"account_service/app/fsm"
	"account_service/app/grpc"
	"account_service/app/models"

	"geti.com/account_service_grpc/pb"
	"github.com/golang/protobuf/ptypes/timestamp"
	"github.com/google/uuid"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
)

var logger = utils.InitializeLogger()

type GRPCServer struct {
	pb.UnimplementedOrganizationStatusServer
	DB grpc.IGormDB
}

func (s *GRPCServer) GetStatuses(_ context.Context, req *pb.OrganizationIdRequest) (*pb.ListOrganizationStatusesResponse, error) {
	logger.Debugf("get statuses request for the organization %s", req.Id)
	orgID, err := uuid.Parse(req.GetId())
	if err != nil {
		logger.Errorf("error during parsing workspace UUID: %v", err)
		return nil, status.Error(codes.InvalidArgument, "malformed workspace UUID")
	}

	var organizationStatusHistories []models.OrganizationStatusHistory
	err = s.DB.Transaction(func(tx *gorm.DB) error {
		if e := tx.Model(&models.OrganizationStatusHistory{}).Where("organization_id = ?", orgID).Find(&organizationStatusHistories).Error; e != nil {
			logger.Errorf("error querying the database: %v", e)
			return status.Error(codes.Unknown, "Unknown error has occurred")
		}

		if len(organizationStatusHistories) != 0 {
			return nil
		}
		var count int64
		if e := tx.Model(&models.Organization{}).Where("id = ?", orgID).Count(&count).Error; e != nil {
			logger.Errorf("error querying the database: %v", e)
			return status.Error(codes.Unknown, "Unknown error has occurred")
		}
		if count == 0 {
			logger.Errorf("Organization not found with ID %v", orgID)
			return status.Error(codes.NotFound, "Organization not found")
		}
		logger.Warnf("Unexpected behavior - for organization with ID %v, no Organization Status History has been found", orgID)
		return nil
	})

	if err != nil {
		return nil, err
	}

	var statuses []*pb.OrganizationStatusResponse
	for _, orgStatus := range organizationStatusHistories {
		statuses = append(statuses, &pb.OrganizationStatusResponse{
			Id:             strconv.FormatUint(uint64(orgStatus.ID), 10),
			Status:         orgStatus.Status,
			OrganizationId: orgStatus.OrganizationID.String(),
			CreatedAt:      timestamppb.New(orgStatus.CreatedAt),
			CreatedBy:      orgStatus.CreatedBy,
		})
	}
	logger.Debugf("statuses response for the organization %s: %v", orgID.String(), statuses)
	return &pb.ListOrganizationStatusesResponse{Statuses: statuses}, nil
}

func (s *GRPCServer) Change(_ context.Context, req *pb.OrganizationStatusRequest) (*pb.OrganizationStatusResponse, error) {
	logger.Debugf("status change request for the organization %s", req.OrganizationId)
	orgRequestedID, err := uuid.Parse(req.OrganizationId)
	if err != nil {
		logger.Errorf("error during parsing workspace uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid workspace UUID: \"%v\" ", req.OrganizationId)
	}

	// Wrap all operations in a transaction
	var resp *pb.OrganizationStatusResponse
	err = s.DB.Transaction(func(tx *gorm.DB) error {
		// Get the organization
		org := models.Organization{ID: orgRequestedID}
		dbResult := tx.First(&org)
		if dbResult.Error != nil {
			logger.Errorf("error during getting organization: %v", dbResult.Error)
			if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
				return status.Errorf(codes.NotFound, "organization ID: \"%v\" not found", org.ID)
			}
			return status.Errorf(codes.Unknown, "unexpected error")
		}
		logger.Debugf("current organization %s status: %s", org.ID.String(), org.Status)

		// Check if passed status is within statuses defined in the ORGANIZATION_STATUSES domain
		// TODO: domains not implemented yet

		err := fsm.OrganizationStatusFSM.Transition(org.Status, req.GetStatus())
		if err != nil {
			logger.Errorf("error validating organization status transition: %v", err)
			return status.Errorf(codes.FailedPrecondition, "incorrect status")
		}

		if req.GetStatus() == "DEL" {
			var userStatusesRelatedToThisOrg []models.UserStatus
			dbResult = tx.Find(&userStatusesRelatedToThisOrg, "organization_id = ? AND current = ?", orgRequestedID, "TRUE")
			if dbResult.Error != nil {
				logger.Errorf("error during getting user status: %v", dbResult.Error)
				return status.Errorf(codes.Unknown, "unexpected error")
			}

			for _, oldUserStatusRelatedToOrg := range userStatusesRelatedToThisOrg {
				err := fsm.UserStatusFSM.Transition(oldUserStatusRelatedToOrg.Status, "DEL")
				if err != nil {
					logger.Errorf("error validating user status transition: %v", err)
					return status.Errorf(codes.FailedPrecondition, "incorrect status")
				}

				oldUserStatusRelatedToOrg.Current = false

				result := tx.Save(&oldUserStatusRelatedToOrg)
				if result.Error != nil {
					logger.Errorf("error during user status update: %v", result.Error)
					return status.Errorf(codes.Unknown, "unexpected error")
				}

				newUserStatus := models.UserStatus{
					Status:         "DEL",
					OrganizationID: oldUserStatusRelatedToOrg.OrganizationID,
					UserID:         oldUserStatusRelatedToOrg.UserID,
					Current:        true,
				}

				result = tx.Create(&newUserStatus)
				if result.Error != nil {
					logger.Errorf("error during user status Create: %v", result.Error)
					return status.Errorf(codes.Unknown, "unexpected error")
				}
			}
		}

		// Update the organization entity with the new status
		org.Status = req.GetStatus()

		if err := tx.Model(&org).Updates(models.Organization{Status: org.Status}).Error; err != nil {
			logger.Errorf("Error ocurred when updating organization with id %v : %v", req.GetOrganizationId(), err)
			return status.Errorf(codes.Unknown, "Unexpected error occurred while updating status of organization with ID %s", req.GetOrganizationId())
		}

		// Add a new record to the organization_status_history entity
		history := models.OrganizationStatusHistory{
			Status:         req.GetStatus(),
			OrganizationID: org.ID,
			CreatedBy:      req.GetCreatedBy(),
		}
		if err := tx.Create(&history).Error; err != nil {
			logger.Errorf("Error ocurred when creating Organization status history for organization with id %v : %v", req.GetOrganizationId(), err)
			return status.Errorf(codes.Unknown, "Unexpected error occurred while updating status history of organization with ID %s", req.GetOrganizationId())
		}

		// Prepare response
		resp = &pb.OrganizationStatusResponse{
			Id:             fmt.Sprint(org.ID),
			Status:         org.Status,
			OrganizationId: req.GetOrganizationId(),
			CreatedAt:      &timestamp.Timestamp{Seconds: org.CreatedAt.Unix(), Nanos: int32(org.CreatedAt.Nanosecond())},
			CreatedBy:      req.GetCreatedBy(),
		}

		// return nil to commit the transaction
		return nil
	})

	if err != nil {
		logger.Errorf("Transaction for the organization status request %v failed: %v", req, err)
		return nil, status.Error(codes.Unknown, "Unknown error while changing the organization status")
	}
	logger.Infof("organization %s status has been changed to %s", req.OrganizationId, req.Status)
	return resp, nil
}
