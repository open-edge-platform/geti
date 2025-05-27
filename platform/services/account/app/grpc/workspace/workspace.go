// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package workspace

import (
	"context"
	"database/sql"
	"errors"
	"fmt"

	"account_service/app/common/utils"
	"account_service/app/config"
	"account_service/app/grpc/common"
	grpcUtils "account_service/app/grpc/utils"
	"account_service/app/models"
	"account_service/app/roles"

	"geti.com/account_service_grpc/pb"

	authzed "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/google/uuid"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
)

var logger = utils.InitializeLogger()

type GRPCServer struct {
	pb.UnimplementedWorkspaceServer
	DB *gorm.DB
}

// Converts the Workspace struct to the WorkspaceData protobuf message.
func workspaceToPb(workspace models.Workspace) *pb.WorkspaceData {
	var modifiedAt *timestamppb.Timestamp
	if workspace.ModifiedAt != nil && workspace.ModifiedAt.Valid {
		modifiedAt = timestamppb.New(workspace.ModifiedAt.Time)
	}

	return &pb.WorkspaceData{
		Id:             workspace.ID.String(),
		Name:           workspace.Name,
		OrganizationId: workspace.OrganizationID.String(),
		CreatedAt:      timestamppb.New(workspace.CreatedAt),
		CreatedBy:      workspace.CreatedBy,
		ModifiedAt:     modifiedAt,
		ModifiedBy:     workspace.ModifiedBy,
	}
}

func CreateWorkspace(tx *gorm.DB, workspace *models.Workspace) error {
	result := tx.Create(&workspace)
	if result.Error != nil {
		logger.Errorf("error during workspace Create: %v", result.Error)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize roles manager: %v", err)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	err = rolesMgr.ChangeOrganizationRelation(
		"workspace",
		workspace.ID.String(),
		[]string{"parent_organization"},
		workspace.OrganizationID.String(),
		authzed.RelationshipUpdate_OPERATION_CREATE)
	if err != nil {
		logger.Errorf("failed to create parent_organization relation for workspace: %v", err)
		return status.Errorf(codes.Unknown, "unexpected error")
	}
	logger.Infof("workspace %s has been successfully created, parent organization id: %s",
		workspace.ID.String(), workspace.OrganizationID.String())

	return nil
}

func (s *GRPCServer) Create(ctx context.Context, data *pb.WorkspaceData) (*pb.WorkspaceData, error) {
	logger.Info("workspace Create request")
	parsedOrganizationUUID, err := uuid.Parse(data.OrganizationId)
	if err != nil {
		logger.Errorf("error during parsing organization UUID: %v", err)
		return nil, status.Error(codes.InvalidArgument, "malformed organization UUID")
	}
	workspace := models.Workspace{
		Name:           data.Name,
		OrganizationID: parsedOrganizationUUID,
		ModifiedAt: &sql.NullTime{
			Valid: false,
		},
		CreatedBy: data.CreatedBy,
	}

	authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
	if ok {
		workspace.CreatedBy = authTokenData.UserID
	}

	err = CreateWorkspace(s.DB, &workspace)
	if err != nil {
		return nil, err
	}

	return workspaceToPb(workspace), nil
}

func (s *GRPCServer) Delete(_ context.Context, req *pb.WorkspaceIdRequest) (*emptypb.Empty, error) {
	logger.Info("workspace Delete request: organization ID %s, workspace ID %s", req.OrganizationId, req.Id)
	parsedWorkspaceUUID, err := uuid.Parse(req.Id)
	if err != nil {
		logger.Errorf("error during parsing workspace UUID: %v", err)
		return nil, status.Error(codes.InvalidArgument, "malformed workspace UUID")
	}

	relFilter := authzed.RelationshipFilter{
		ResourceType:       "workspace",
		OptionalResourceId: parsedWorkspaceUUID.String(),
	}

	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize roles manager: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	workspaceRelationships, err := rolesMgr.GetRelationships(&relFilter)
	if err != nil {
		logger.Errorf("unable to get workspace's relationships: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}
	for _, relationship := range workspaceRelationships {
		subjectType := relationship.GetSubject().GetObject().GetObjectType()
		switch subjectType {
		case "organization":
			err := rolesMgr.ChangeOrganizationRelation(relationship.Resource.ObjectType,
				relationship.Resource.ObjectId, []string{relationship.Relation}, relationship.Subject.Object.ObjectId,
				authzed.RelationshipUpdate_OPERATION_DELETE)
			if err != nil {
				logger.Errorf("failed to delete organization relationships: %v", err)
				return nil, status.Errorf(codes.Unknown, "unexpected error")
			}
		case "user":
			err := rolesMgr.ChangeUserRelation(relationship.Resource.ObjectType,
				relationship.Resource.ObjectId, []string{relationship.Relation}, relationship.Subject.Object.ObjectId,
				authzed.RelationshipUpdate_OPERATION_DELETE)
			if err != nil {
				logger.Errorf("failed to delete user relationships: %v", err)
				return nil, status.Errorf(codes.Unknown, "unexpected error")
			}
		default:
			logger.Errorf("unknown subject type relationships to delete: %v", subjectType)
			return nil, status.Errorf(codes.Unknown, "unexpected error")
		}
	}

	dbResult := s.DB.Delete(&models.Workspace{ID: parsedWorkspaceUUID})
	if dbResult.Error != nil {
		logger.Errorf("error during deleting workspace: %v", dbResult.Error)
		return nil, status.Error(codes.Unknown, "unexpected error occurred while deleting workspace")
	}

	if dbResult.RowsAffected == 0 {
		logger.Errorf("No workspace found to delete for the UUID: %v", parsedWorkspaceUUID.String())
		return nil, status.Error(codes.NotFound, "No workspace found to delete")
	}
	logger.Infof("workspace %s has been deleted from organization %s", req.Id, req.OrganizationId)
	return &emptypb.Empty{}, nil
}

func (s *GRPCServer) Modify(ctx context.Context, data *pb.WorkspaceData) (*pb.WorkspaceData, error) {
	logger.Debugf("workspace modify request: %v", data)

	workspace := models.Workspace{}
	workspaceRequestedID, err := uuid.Parse(data.Id)
	if err != nil {
		logger.Errorf("error during parsing workspace uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid workspace UUID: \"%v\" ", data.Id)
	}

	transactionFunc := func(tx *gorm.DB) error {
		dbResult := tx.First(&workspace, "id = ?", workspaceRequestedID.String())
		if dbResult.Error != nil {
			logger.Errorf("error during getting workspace in modify transaction: %v", dbResult.Error)
			if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
				return status.Errorf(codes.NotFound, "workspace ID: \"%v\" not found", workspaceRequestedID.String())
			}
			return status.Error(codes.Unknown, "unexpected error")
		}

		workspace.Name = data.Name
		workspaceOrganizationID, err := uuid.Parse(data.OrganizationId)
		if err != nil {
			logger.Errorf("error during parsing organization uuid: %v", err)
			return status.Errorf(codes.InvalidArgument, "invalid organization UUID: \"%v\" ", data.OrganizationId)
		}
		workspace.OrganizationID = workspaceOrganizationID
		workspace.ModifiedBy = data.ModifiedBy

		authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if ok {
			workspace.ModifiedBy = authTokenData.UserID
		}

		result := tx.Updates(&workspace)
		if result.Error != nil {
			logger.Errorf("error during workspace update: %v", result.Error)
			if grpcUtils.ErrorIsPGUniqueViolation(result.Error, "workspaces_name_key") {
				return status.Errorf(codes.AlreadyExists, "workspace \"%v\" already exists", data.Name)
			}
			return status.Error(codes.Unknown, "unexpected error")
		}
		return nil
	}

	err = s.DB.Transaction(transactionFunc)
	if err != nil {
		return nil, err
	}

	return workspaceToPb(workspace), nil
}

func (s *GRPCServer) GetById(_ context.Context, req *pb.WorkspaceIdRequest) (*pb.WorkspaceData, error) {
	logger.Debugf("get workspace request - organization ID %s, workspace ID %s", req.OrganizationId, req.Id)
	workspaceRequestedID, err := uuid.Parse(req.Id)
	if err != nil {
		logger.Errorf("error during parsing workspace uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid workspace UUID: \"%v\" ", req.Id)
	}

	workspace := models.Workspace{ID: workspaceRequestedID}

	dbResult := s.DB.First(&workspace)
	if dbResult.Error != nil {
		logger.Errorf("error during getting workspace: %v", dbResult.Error)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return nil, status.Errorf(codes.NotFound, "workspace ID: \"%v\" not found", req.Id)
		}
		return nil, status.Error(codes.Unknown, "unexpected error")
	}

	return workspaceToPb(workspace), nil
}

func (s *GRPCServer) Find(ctx context.Context, findRequest *pb.FindWorkspaceRequest) (*pb.ListWorkspacesResponse, error) {
	logger.Debugf("find workspace request: %v", findRequest)

	var workspaces []models.Workspace
	statementSession := s.DB.WithContext(ctx)
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
			"created_at BETWEEN ? AND ?", findRequest.CreatedAtFrom.AsTime(), findRequest.CreatedAtTo.AsTime(),
		)
	} else if findRequest.CreatedAtFrom != nil {
		statementSession = statementSession.Where("created_at > ?", findRequest.CreatedAtFrom.AsTime())
	} else if findRequest.CreatedAtTo != nil {
		statementSession = statementSession.Where("created_at < ?", findRequest.CreatedAtTo.AsTime())
	}
	if findRequest.CreatedBy != "" {
		statementSession = statementSession.Where("created_by = ?", findRequest.CreatedBy)
	}

	if findRequest.ModifiedAtFrom != nil && findRequest.ModifiedAtTo != nil {
		statementSession = statementSession.Where(
			"modified_at BETWEEN ? AND ?", findRequest.ModifiedAtFrom.AsTime(), findRequest.ModifiedAtTo.AsTime(),
		)
	} else if findRequest.ModifiedAtFrom != nil {
		statementSession = statementSession.Where("modified_at > ?", findRequest.ModifiedAtFrom.AsTime())
	} else if findRequest.ModifiedAtTo != nil {
		statementSession = statementSession.Where("modified_at < ?", findRequest.ModifiedAtTo.AsTime())
	}
	if findRequest.ModifiedBy != "" {
		statementSession = statementSession.Where("modified_by = ?", findRequest.ModifiedBy)
	}

	if findRequest.SortBy != "" && findRequest.SortDirection != "" {
		orderQuery, err := common.CreateOrderQuery(models.Workspace{}, findRequest.SortBy, findRequest.SortDirection)
		if err != nil {
			return nil, err
		}
		statementSession = statementSession.Order(orderQuery)
	}

	var totalMatchedCount int64
	dbResult := statementSession.Count(&totalMatchedCount)
	if dbResult.Error != nil {
		logger.Errorf("error during workspace count: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
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
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	response := pb.ListWorkspacesResponse{}
	for _, workspaceModel := range workspaces {
		workspaceData := workspaceToPb(workspaceModel) // function to convert workspace model to protobuf model
		response.Workspaces = append(response.Workspaces, workspaceData)
	}

	response.TotalMatchedCount = int32(totalMatchedCount)

	nextPageFields := common.CalculateNextPage(response.TotalMatchedCount, findRequest.Skip, findRequest.Limit)

	totalCount, err := common.CountAll(s.DB, models.Workspace{})
	if err != nil {
		logger.Errorf("error during workspace count: %v", dbResult.Error)
		return nil, err
	}

	response.TotalCount = totalCount

	nextPage := pb.ListWorkspacesResponse_NextPage{
		Skip:  nextPageFields.Skip,
		Limit: nextPageFields.Limit,
	}

	response.NextPage = &nextPage

	return &response, nil
}
