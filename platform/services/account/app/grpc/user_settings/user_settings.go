// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package user_settings

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"

	"github.com/google/uuid"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"

	"account_service/app/grpc/common"
	grpcUtils "account_service/app/grpc/utils"
	"account_service/app/grpc_gateway"
	"account_service/app/models"
	"common/utils"

	"geti.com/account_service_grpc/pb"
)

var logger = utils.InitializeLogger()

type GRPCServer struct {
	pb.UnimplementedUserSettingsServiceServer
	DB *gorm.DB
}

func (s *GRPCServer) Create(ctx context.Context, req *pb.UserSettingsCreateRequest) (*pb.UserSettingsResponse, error) {
	logger.Debugf("POST /user_settings request received: %v", req)
	authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
	if !ok {
		logger.Errorf("Failed to retrieve auth token data: %v", authTokenData)
		return nil, status.Error(codes.Unknown, "unexpected error while creating user settings")
	}

	userId, err := uuid.Parse(authTokenData.UserID)
	if err != nil {
		logger.Errorf("error during parsing user UUID: %v", err)
		return nil, status.Error(codes.InvalidArgument, "malformed user UUID")
	}

	orgId, err := uuid.Parse(authTokenData.OrgID)
	if err != nil {
		logger.Errorf("error during parsing organization UUID: %v", err)
		return nil, status.Error(codes.InvalidArgument, "malformed organization UUID")
	}

	var projectId *string
	if req.ProjectId != "" {
		projectId = &req.ProjectId
	}

	if len(req.Settings.GetSettings()) > 3000 {
		return nil, status.Error(codes.InvalidArgument, "Settings provided exceed the maximum of 3000 characters")
	}

	var userSettings models.UserSettings
	changeState := ""

	err = s.DB.Transaction(func(tx *gorm.DB) error {
		statementSession := tx.WithContext(ctx).Model(&userSettings).
			Where("user_id = ? AND organization_id = ?", userId, orgId)

		if req.GetProjectId() != "" {
			logger.Debugf("Project ID in the request: %v", req.ProjectId)
			statementSession = statementSession.Where("project_id = ?", req.ProjectId)
		} else {
			logger.Debug("Project ID is missing in the request - looking for record with NULL project_id")
			statementSession = statementSession.Where("project_id is NULL")
		}

		dbResult := statementSession.First(&userSettings)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			changeState = "created"
			userSettings = models.UserSettings{
				Data:           json.RawMessage(req.Settings.GetSettings()),
				UserID:         userId,
				OrganizationID: orgId,
				ProjectID:      projectId,
				ModifiedBy:     userId.String(),
			}
			logger.Debugf("Creating user settings with following data: %v", userSettings)
			return tx.Create(&userSettings).Error
		} else if dbResult.Error != nil {
			logger.Errorf("Unexpected error while returning user settings row: %v", dbResult.Error)
			return status.Errorf(codes.Unknown, "unexpected Error")
		}

		changeState = "updated"
		userSettings.Data = json.RawMessage(req.Settings.GetSettings())
		userSettings.ProjectID = projectId
		userSettings.ModifiedBy = userId.String()
		logger.Debugf("Updating user settings with following data: %v", userSettings)
		return tx.Save(&userSettings).Error
	})

	if err != nil {
		logger.Errorf("error during POST user settings operation: %v", err)
		return nil, status.Error(codes.Unknown, "unexpected error")
	}

	return &pb.UserSettingsResponse{
		Message: fmt.Sprintf("User settings successfully %s", changeState),
	}, nil
}

func (s *GRPCServer) Get(ctx context.Context, request *pb.UserSettingsRequest) (*pb.UserSettings, error) {
	logger.Debugf("GET /user_settings request received %#v", request)
	authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
	if !ok {
		logger.Errorf("error during parsing organization uuid and user uuid from internal token")
		return nil, status.Error(codes.Unknown, "unexpected error")
	}
	parsedOrganizationUUID, err := uuid.Parse(authTokenData.OrgID)
	if err != nil {
		logger.Errorf("error during parsing organization uuid: %v", err)
		return nil, status.Error(codes.InvalidArgument, "invalid organization UUID")
	}

	parsedUserUUID, err := uuid.Parse(authTokenData.UserID)
	if err != nil {
		logger.Errorf("error during parsing user uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid user UUID")
	}

	userSettings := models.UserSettings{}
	statementSession := s.DB.WithContext(ctx)
	statementSession = statementSession.Model(&userSettings)

	statementSession = statementSession.Where("organization_id = ? AND user_id = ?", parsedOrganizationUUID.String(), parsedUserUUID.String())

	if request.ProjectId != "" {
		logger.Debugf("Received project_id in a request: %v", request.ProjectId)
		statementSession = statementSession.Where("project_id = ?", request.GetProjectId())
	} else {
		logger.Debugf("Missing project id from a request - looking for NULL row")
		statementSession = statementSession.Where("project_id is NULL")
	}

	logger.Debugf("Statement session before GET request %#v", statementSession.Statement)
	dbResult := statementSession.First(&userSettings)
	if dbResult.Error != nil {
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			logger.Debugf("GET /user_settings did not find record for %+v, %+v, %+v", parsedOrganizationUUID, parsedUserUUID, request.GetProjectId())
			grpc_gateway.SetCustomHTTPResponseStatusCode(ctx, http.StatusNoContent)
			return nil, nil
		}
		logger.Errorf("error during getting user settings: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	jsonData, err := userSettings.Data.MarshalJSON()
	if err != nil {
		logger.Errorf("error marshalling user settings: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	userSettingsResponse := pb.UserSettings{
		Id:             userSettings.ID.String(),
		UserId:         userSettings.UserID.String(),
		OrganizationId: userSettings.OrganizationID.String(),
		Settings:       string(jsonData),
		CreatedAt:      timestamppb.New(userSettings.CreatedAt),
		CreatedBy:      userSettings.CreatedBy,
		ModifiedAt:     common.SqlTimeToTimestamp(userSettings.ModifiedAt),
		ModifiedBy:     userSettings.ModifiedBy,
	}
	logger.Debugf("Retrieving record containing %#v", &userSettingsResponse)

	return &userSettingsResponse, nil
}
