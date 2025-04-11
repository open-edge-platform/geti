// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package organization

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"html/template"
	"io"
	"strings"
	"time"

	"account_service/app/config"
	"account_service/app/fsm"
	"account_service/app/grpc/common"
	"account_service/app/grpc/user"
	grpcUtils "account_service/app/grpc/utils"
	"account_service/app/grpc/workspace"
	"account_service/app/messaging"
	"account_service/app/models"
	"account_service/app/roles"
	"account_service/app/services"
	membershipService "account_service/app/services/membership"
	orgService "account_service/app/services/organization"
	"account_service/app/storage"
	"common/utils"

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
	pb.UnimplementedOrganizationServer
	DB                  *gorm.DB
	OrganizationService orgService.Service
	MembershipService   membershipService.MembershipService
}

func organizationToPb(org models.Organization) *pb.OrganizationData {
	var modifiedAt *timestamppb.Timestamp
	if org.ModifiedAt != nil && org.ModifiedAt.Valid {
		modifiedAt = timestamppb.New(org.ModifiedAt.Time)
	}

	return &pb.OrganizationData{
		Id:                  org.ID.String(),
		Name:                org.Name,
		Country:             org.Country,
		Location:            org.Location,
		Type:                org.Type,
		CellId:              org.CellID,
		Status:              org.Status,
		CreatedAt:           timestamppb.New(org.CreatedAt),
		CreatedBy:           org.CreatedBy,
		ModifiedAt:          modifiedAt,
		ModifiedBy:          org.ModifiedBy,
		RequestAccessReason: org.RequestAccessReason,
	}
}

func organizationWithAdminsToPb(org models.Organization, organizationAdmins []*models.User) *pb.OrganizationDataWithAdmins {
	organizationData := organizationToPb(org)
	admins := make([]*pb.OrganizationDataWithAdmins_AdminSimpleData, len(organizationAdmins))
	for i, admin := range organizationAdmins {
		adminData := &pb.OrganizationDataWithAdmins_AdminSimpleData{
			FirstName: admin.FirstName,
			LastName:  admin.SecondName,
			Email:     admin.Email,
		}
		admins[i] = adminData
	}

	return &pb.OrganizationDataWithAdmins{
		Id:                  organizationData.Id,
		Name:                organizationData.Name,
		Country:             organizationData.Country,
		Location:            organizationData.Location,
		Type:                organizationData.Type,
		CellId:              organizationData.CellId,
		Status:              organizationData.Status,
		CreatedAt:           organizationData.CreatedAt,
		CreatedBy:           organizationData.CreatedBy,
		ModifiedAt:          organizationData.ModifiedAt,
		ModifiedBy:          organizationData.ModifiedBy,
		Admins:              admins,
		RequestAccessReason: organizationData.RequestAccessReason,
	}
}

func CountOrganizationStatuses(tx *gorm.DB) (map[string]int64, error) {
	var results []struct {
		Status string
		Count  int64
	}

	// Perform the query to count organizations grouped by status
	dbResult := tx.Model(&models.Organization{}).
		Select("status, COUNT(*) as count").
		Group("status").
		Scan(&results)

	if dbResult.Error != nil {
		logger.Errorf("error during counting organization states: %v", dbResult.Error)
		return nil, dbResult.Error
	}

	// Create a map to hold the results
	statusCounts := make(map[string]int64)
	for _, result := range results {
		statusCounts[result.Status] = result.Count
	}

	return statusCounts, nil
}

func getOrganizationAdmins(tx *gorm.DB, orgID string) ([]*models.User, error) {
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize client: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	adminsRelationships, err := rolesMgr.GetOrganizationRelationships(orgID, "organization_admin")
	if err != nil {
		logger.Errorf("error during getting organization admin relationships: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	organizationAdmins := make([]*models.User, len(adminsRelationships))

	for i, adminRelationship := range adminsRelationships {
		adminUserID := adminRelationship.Subject.Object.ObjectId
		adminUser, err := user.GetUserFromDBByID(tx, adminUserID)
		if err != nil {
			logger.Errorf("error during getting user organization admin: %v", err)
			return nil, status.Errorf(codes.Unknown, "unexpected error")
		}

		organizationAdmins[i] = adminUser
	}

	return organizationAdmins, nil
}

func (s *GRPCServer) Create(ctx context.Context, data *pb.OrganizationData) (*pb.OrganizationData, error) {
	logger.Info("organization Create request")
	org := models.Organization{
		Name:     data.Name,
		Country:  data.Country,
		Location: data.Location,
		Type:     data.Type,
		CellID:   data.CellId,
		Status:   data.Status,
		ModifiedAt: &sql.NullTime{
			Valid: false,
		},
		CreatedBy:           data.CreatedBy,
		RequestAccessReason: data.RequestAccessReason,
	}

	authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
	if ok {
		org.CreatedBy = authTokenData.UserID
	}

	err := s.OrganizationService.CreateOrganization(&org)
	if err != nil {
		var aerr *services.AlreadyExistsError
		ok := errors.As(err, &aerr)
		if ok {
			return nil, status.Errorf(codes.AlreadyExists, "organization \"%v\" already exists", org.Name)
		}
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	return organizationToPb(org), nil
}

func sendActivationMessage(membership models.MembershipResult, topic string, mailMessage string) error {
	type InvitationFilling struct {
		InvitationLink string
	}

	filling := InvitationFilling{
		InvitationLink: config.InvitationLink,
	}

	tmpl, err := template.New("invitation").Parse(mailMessage)
	if err != nil {
		logger.Errorf("error during parsing invitation template: %v", err)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	var invitationMessage bytes.Buffer
	err = tmpl.Execute(&invitationMessage, filling)
	if err != nil {
		logger.Errorf("error during executing invitation template: %v", err)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	message := map[string]string{
		"subject":      topic,
		"to":           membership.Email,
		"from_address": config.InvitationFromAddress,
		"from_name":    config.InvitationFromName,
		"content":      "",
		"html_content": invitationMessage.String(),
	}

	jsonMsg, err := json.Marshal(message)
	if err != nil {
		logger.Errorf("error during marshalling invitation message: %v", err)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	err = messaging.SendMessage(config.KafkaTopicPrefix+config.GetiNotificationTopic, jsonMsg)
	if err != nil {
		logger.Errorf("error during pushing invitation message to queue: %v", err)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	return nil
}

func ModifyOrganizationUsers(s *GRPCServer, ctx context.Context, membership models.MembershipResult, org *pb.OrganizationData) error {
	_, err := s.MembershipService.SetUserStatus(ctx, membership.UserID, uuid.MustParse(org.Id), org.Status)
	if err != nil {
		logger.Errorf("error during processing REQ users: %v", err)
		return status.Errorf(codes.Unknown, "unexpected error: %v", err)
	}
	if org.Status == "ACT" {
		errSend := sendActivationMessage(membership, config.OrganizationAcceptRequestedAccessTopic, config.OrganizationAcceptRequestedAccessMessage)
		if errSend != nil {
			return status.Errorf(codes.Unknown, "unexpected error: %v", err)
		}
	} else if org.Status == "DEL" {
		errSend := sendActivationMessage(membership, config.OrganizationRejectRequestedAccessTopic, config.OrganizationRejectRequestedAccessMessage)
		if errSend != nil {
			return status.Errorf(codes.Unknown, "unexpected error: %v", err)
		}
	}
	return nil
}

func (s *GRPCServer) Modify(ctx context.Context, data *pb.OrganizationData) (*pb.OrganizationData, error) {
	logger.Debugf("organization Modify request with data: %v", data)
	requestedId := data.Id
	org := models.Organization{}

	transactionFunc := func(tx *gorm.DB) error {
		dbResult := tx.First(&org, "id = ?", requestedId)
		if dbResult.Error != nil {
			logger.Errorf("error during getting organization in modify transaction: %v", dbResult.Error)
			if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
				return status.Errorf(codes.NotFound, "organization ID: \"%v\" not found", requestedId)
			}
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		org.Name = data.Name
		org.Country = data.Country
		org.Location = data.Location
		org.Type = data.Type
		org.CellID = data.CellId
		org.ModifiedBy = data.ModifiedBy
		org.RequestAccessReason = data.RequestAccessReason

		authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if ok {
			org.ModifiedBy = authTokenData.UserID
		}

		if data.Status != "" && org.Status != data.Status {
			logger.Infof("changing organization %s status from %s to %s", org.ID, org.Status, data.Status)
			err := fsm.OrganizationStatusFSM.Transition(org.Status, data.Status)
			if err != nil {
				logger.Errorf("error validating organization status transition: %v", err)
				return status.Errorf(codes.FailedPrecondition, "incorrect status")
			}

			if org.Status == "REQ" && config.FeatureFlagReqAccess {
				logger.Info("Activating Requested organization with users")
				memberReq := &pb.MembershipRequest{OrganizationId: org.ID.String()}
				memberships, _, err := s.MembershipService.GetMemberships(ctx, memberReq)
				if err != nil {
					logger.Errorf("error during getting REQ users: %v", err)
					return status.Errorf(codes.Unknown, "unexpected error: %v", err)
				}
				for _, membership := range memberships {
					err := ModifyOrganizationUsers(s, ctx, membership, data)
					if err != nil {
						logger.Errorf("error during processing REQ user message: %v", err)
						return status.Errorf(codes.Unknown, "unexpected error: %v", err)
					}
				}
			}
			if data.Status == "DEL" {
				var userStatusesRelatedToThisOrg []models.UserStatus
				dbResult = tx.Find(&userStatusesRelatedToThisOrg, "organization_id = ? AND current = ?", requestedId, "TRUE")
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

						return status.Errorf(codes.Unknown, "unexpected error")
					}
				}
			}

			org.Status = data.Status

			orgStatusHistoryEntry := models.OrganizationStatusHistory{
				Status:         data.Status,
				OrganizationID: org.ID,
			}

			result := tx.Create(&orgStatusHistoryEntry)
			if result.Error != nil {
				logger.Errorf("error during organization status history Create: %v", result.Error)
				return status.Errorf(codes.Unknown, "unexpected error")
			}
		}

		result := tx.Updates(&org)
		if result.Error != nil {
			logger.Errorf("error during organization update: %v", result.Error)
			if grpcUtils.ErrorIsPGUniqueViolation(result.Error, "organizations_name_key") {
				return status.Errorf(codes.AlreadyExists, "organization \"%v\" already exists", data.Name)
			}
			return status.Errorf(codes.Unknown, "unexpected error")
		}
		return nil
	}

	err := s.DB.Transaction(transactionFunc)
	if err != nil {
		logger.Errorf("failed to update the organization %s: %v", org.ID, err)
		return nil, err
	}

	return organizationToPb(org), nil
}

func (s *GRPCServer) GetById(_ context.Context, req *pb.OrganizationIdRequest) (*pb.OrganizationDataWithAdmins, error) {
	logger.Debugf("get organization request for organization id %s", req.Id)
	org := models.Organization{}

	orgRequestedID, err := uuid.Parse(req.Id)
	if err != nil {
		logger.Errorf("error during parsing organization uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid organization UUID: \"%v\" ", req.Id)
	}

	dbResult := s.DB.First(&org, "id = ?", orgRequestedID.String())
	if dbResult.Error != nil {
		logger.Errorf("error during getting organization: %v", dbResult.Error)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return nil, status.Errorf(codes.NotFound, "organization ID: \"%v\" not found", req.Id)
		}
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	organizationAdmins, err := getOrganizationAdmins(s.DB, org.ID.String())
	if err != nil {
		return nil, err
	}

	return organizationWithAdminsToPb(org, organizationAdmins), nil
}

func (s *GRPCServer) Find(ctx context.Context, findRequest *pb.FindOrganizationRequest) (*pb.ListOrganizationsResponse, error) {
	logger.Debugf("Find organization request: %v", findRequest)
	var orgs []models.Organization

	statementSession := s.DB.WithContext(ctx)
	statementSession = statementSession.Model(&orgs)

	if findRequest.Id != "" {
		statementSession = statementSession.Where("organizations.id = ?", findRequest.Id)
	}
	if findRequest.Country != "" {
		statementSession = statementSession.Where("organizations.country = ?", findRequest.Country)
	}
	if findRequest.Location != "" {
		statementSession = statementSession.Where("LOWER(organizations.location) = LOWER(?)", findRequest.Location)
	}
	if findRequest.Type != "" {
		statementSession = statementSession.Where("organizations.type = ?", findRequest.Type)
	}
	if findRequest.CellId != "" {
		statementSession = statementSession.Where("LOWER(organizations.cell_id) = LOWER(?)", findRequest.CellId)
	}
	if findRequest.Status != "" {
		statementSession = statementSession.Where("organizations.status = ?", findRequest.Status)
	}

	if findRequest.CreatedAtFrom != nil && findRequest.CreatedAtTo != nil {
		statementSession = statementSession.Where(
			"organizations.created_at BETWEEN ? AND ?", findRequest.CreatedAtFrom.AsTime(), findRequest.CreatedAtTo.AsTime(),
		)
	} else if findRequest.CreatedAtFrom != nil {
		statementSession = statementSession.Where("organizations.created_at > ?", findRequest.CreatedAtFrom.AsTime())
	} else if findRequest.CreatedAtTo != nil {
		statementSession = statementSession.Where("organizations.created_at < ?", findRequest.CreatedAtTo.AsTime())
	}
	if findRequest.CreatedBy != "" {
		statementSession = statementSession.Where("organizations.created_by = ?", findRequest.CreatedBy)
	}

	if findRequest.ModifiedAtFrom != nil && findRequest.ModifiedAtTo != nil {
		statementSession = statementSession.Where(
			"organizations.modified_at BETWEEN ? AND ?", findRequest.ModifiedAtFrom.AsTime(), findRequest.ModifiedAtTo.AsTime(),
		)
	} else if findRequest.ModifiedAtFrom != nil {
		statementSession = statementSession.Where("organizations.modified_at > ?", findRequest.ModifiedAtFrom.AsTime())
	} else if findRequest.ModifiedAtTo != nil {
		statementSession = statementSession.Where("organizations.modified_at < ?", findRequest.ModifiedAtTo.AsTime())
	}

	if findRequest.ModifiedBy != "" {
		statementSession = statementSession.Where("organizations.modified_by = ?", findRequest.ModifiedBy)
	}

	if findRequest.RequestAccessReason != "" {
		statementSession = statementSession.Where("organizations.request_access_reason LIKE ?", findRequest.RequestAccessReason)
	}

	if config.FeatureFlagManageUsers && findRequest.Name != "" {
		// when manage users flag is enabled - filter based a name in SQL query
		statementSession = statementSession.Joins("left outer join user_statuses on organizations.id = user_statuses.organization_id and user_statuses.current = ?", "TRUE")
		statementSession = statementSession.Joins("left outer join users on user_statuses.user_id = users.id")
		statementSession = statementSession.Where("LOWER(organizations.name) LIKE ? or LOWER(users.first_name) LIKE ? or LOWER(users.second_name) LIKE ? or LOWER(users.email) LIKE ?",
			"%"+strings.ToLower(findRequest.Name)+"%",
			"%"+strings.ToLower(findRequest.Name)+"%",
			"%"+strings.ToLower(findRequest.Name)+"%",
			"%"+strings.ToLower(findRequest.Name)+"%")
		statementSession = statementSession.Group("organizations.id")
	}

	if findRequest.SortBy != "" && findRequest.SortDirection != "" {
		orderQuery, err := common.CreateOrderQuery(models.Organization{}, findRequest.SortBy, findRequest.SortDirection)
		if err != nil {
			logger.Errorf("couldn't create order query for the find organization request. %v", err)
			return nil, err
		}
		statementSession = statementSession.Order(orderQuery).Order("id")

	}

	var totalMatchedCount int64

	// This is for performance optimization - we can't limit/offset in SQL query if filtering by name,
	// but in other cases, we can (this code below is for all these other cases).
	// It could be simplified if not this branching for optimization.
	if findRequest.Name == "" || config.FeatureFlagManageUsers {
		// In case where no name param is provided, we can apply limit offset but first totalMatchedCount has to be counted.
		dbResult := statementSession.Count(&totalMatchedCount)
		if dbResult.Error != nil {
			// when wrong format of id parameter is given - return http 400 instead of 500
			if strings.Contains(dbResult.Error.Error(), "invalid input syntax for type uuid") {
				logger.Errorf("invalid input syntax for type uuid: %v", dbResult.Error)
				return nil, status.Errorf(codes.InvalidArgument, "invalid argument")
			}
			logger.Errorf("error during organization count: %v", dbResult.Error)
			return nil, status.Errorf(codes.Unknown, "unexpected error")
		}

		if findRequest.Skip > 0 {
			statementSession = statementSession.Offset(int(findRequest.Skip))
		}
		if findRequest.Limit > 0 {
			statementSession = statementSession.Limit(int(findRequest.Limit))
		}
	}
	dbResult := statementSession.Find(&orgs)

	if dbResult.Error != nil {
		logger.Errorf("error during organization find: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	var filteredOrgIDs []string
	response := pb.ListOrganizationsResponse{}
	matchedCount := 0

	if !config.FeatureFlagManageUsers {
		for _, orgModel := range orgs {
			organizationAdmins, err := getOrganizationAdmins(s.DB, orgModel.ID.String())
			if err != nil {
				return nil, err
			}

			// Apply `findRequest.Name` filtering after retrieving the data
			if findRequest.Name != "" {
				matches := false

				// Check if organization name or ID matches
				if strings.Contains(strings.ToLower(orgModel.Name), strings.ToLower(findRequest.Name)) ||
					strings.EqualFold(orgModel.ID.String(), findRequest.Name) {
					matches = true
				}

				// Check if any admin details match
				for _, admin := range organizationAdmins {
					if strings.Contains(strings.ToLower(admin.Email), strings.ToLower(findRequest.Name)) ||
						strings.Contains(strings.ToLower(admin.FirstName), strings.ToLower(findRequest.Name)) ||
						strings.Contains(strings.ToLower(admin.SecondName), strings.ToLower(findRequest.Name)) {
						matches = true
						break
					}
				}

				if !matches {
					continue
				}
			}

			filteredOrgIDs = append(filteredOrgIDs, orgModel.ID.String())

			// In case where Name was provided, we didn't apply limit/offset values previously,
			// so it has to be done in the code
			if findRequest.Name != "" {
				matchedCount++
				if matchedCount <= int(findRequest.Skip) {
					continue
				}
				if findRequest.Limit > 0 && len(response.Organizations) >= int(findRequest.Limit) {
					break
				}
			}

			response.Organizations = append(response.Organizations, organizationWithAdminsToPb(orgModel, organizationAdmins))
		}
	} else {
		// extend organization data with admin data
		for _, orgModel := range orgs {
			organizationAdmins, err := getOrganizationAdmins(s.DB, orgModel.ID.String())
			if err != nil {
				return nil, err
			}
			filteredOrgIDs = append(filteredOrgIDs, orgModel.ID.String())
			response.Organizations = append(response.Organizations, organizationWithAdminsToPb(orgModel, organizationAdmins))
		}
	}

	// We can't count total matched count before we perform filtering in the code.
	if len(filteredOrgIDs) > 0 && findRequest.Name != "" && !config.FeatureFlagManageUsers {
		// Update `statementSession` to filter by IDs that passed the additional checks
		statementSession = statementSession.Where("organizations.id IN (?)", filteredOrgIDs)
		dbResult = statementSession.Count(&totalMatchedCount)
		if dbResult.Error != nil {
			logger.Errorf("error during organization count: %v", dbResult.Error)
			return nil, status.Errorf(codes.Unknown, "unexpected error")
		}
	}

	response.TotalMatchedCount = int32(totalMatchedCount)

	nextPageFields := common.CalculateNextPage(response.TotalMatchedCount, findRequest.Skip, findRequest.Limit)

	totalCount, err := common.CountAll(s.DB, models.Organization{})
	if err != nil {
		logger.Errorf("error during organization count: %v", dbResult.Error)
		return nil, err
	}

	response.TotalCount = totalCount

	nextPage := pb.ListOrganizationsResponse_NextPage{
		Skip:  nextPageFields.Skip,
		Limit: nextPageFields.Limit,
	}

	response.NextPage = &nextPage

	return &response, nil
}

func (s *GRPCServer) Delete(_ context.Context, req *pb.OrganizationIdRequest) (*emptypb.Empty, error) {
	logger.Infof("Delete request for the organization %s", req.Id)
	parsedOrganizationUUID, err := uuid.Parse(req.Id)
	if err != nil {
		logger.Errorf("error during parsing organization UUID: %v", err)
		return nil, status.Error(codes.InvalidArgument, "malformed organization UUID")
	}

	var workspacesToBeCascadeDeleted []models.Workspace

	dbResult := s.DB.Where("organization_id = ?", parsedOrganizationUUID.String()).Find(&workspacesToBeCascadeDeleted)
	if dbResult.Error != nil {
		logger.Errorf("error during workspace find query: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize roles manager: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	for _, workspaceToBeDeleted := range workspacesToBeCascadeDeleted {
		relFilter := authzed.RelationshipFilter{
			ResourceType:       "workspace",
			OptionalResourceId: workspaceToBeDeleted.ID.String(),
		}
		workspaceRelationships, err := rolesMgr.GetRelationships(&relFilter)
		if err != nil {
			logger.Errorf("unable to get workspace's relationships: %v", err)
			return nil, status.Errorf(codes.Unknown, "unexpected error")
		}
		for _, relationship := range workspaceRelationships {
			subjectType := relationship.GetSubject().GetObject().GetObjectType()
			if subjectType == "organization" {
				err := rolesMgr.ChangeOrganizationRelation(relationship.Resource.ObjectType,
					relationship.Resource.ObjectId, []string{relationship.Relation}, relationship.Subject.Object.ObjectId,
					authzed.RelationshipUpdate_OPERATION_DELETE)
				if err != nil {
					logger.Errorf("failed to delete organization relationships: %v", err)
					return nil, status.Errorf(codes.Unknown, "unexpected error")
				}
			} else if subjectType == "user" {
				err := rolesMgr.ChangeUserRelation(relationship.Resource.ObjectType,
					relationship.Resource.ObjectId, []string{relationship.Relation}, relationship.Subject.Object.ObjectId,
					authzed.RelationshipUpdate_OPERATION_DELETE)
				if err != nil {
					logger.Errorf("failed to delete user relationships: %v", err)
					return nil, status.Errorf(codes.Unknown, "unexpected error")
				}
			} else {
				logger.Errorf("unknown subject type relationships to delete: %v", subjectType)
				return nil, status.Errorf(codes.Unknown, "unexpected error")
			}
		}
	}

	dbResult = s.DB.Delete(&models.Organization{ID: parsedOrganizationUUID})
	if dbResult.Error != nil {
		logger.Errorf("error during deleting organization: %v", dbResult.Error)
		return nil, status.Error(codes.Unknown, "unexpected error during deleting organization")
	}

	if dbResult.RowsAffected == 0 {
		logger.Errorf("No organization found to be deleted for the UUID: %v", parsedOrganizationUUID.String())
		return nil, status.Error(codes.NotFound, "No organization found to be deleted")
	}
	logger.Infof("organization %s has been deleted.", parsedOrganizationUUID.String())

	return &emptypb.Empty{}, nil
}

func (s *GRPCServer) AddPhoto(srv pb.Organization_AddPhotoServer) error {
	logger.Debug("Add Photo request")
	req, err := srv.Recv()
	if err != nil {
		logger.Errorf("unexpected error during AddPhoto: %v", err)
		return status.Error(codes.Unknown, "unexpected error during AddPhoto")
	}

	orgId := req.GetUserData().GetId()

	org := models.Organization{}

	orgRequestedID, err := uuid.Parse(orgId)
	if err != nil {
		logger.Errorf("error during parsing organization uuid: %v", err)
		return status.Errorf(codes.InvalidArgument, "invalid organization UUID: \"%v\" ", orgId)
	}

	dbResult := s.DB.First(&org, "id = ?", orgRequestedID.String())
	if dbResult.Error != nil {
		logger.Errorf("error during getting organization: %v", dbResult.Error)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return status.Errorf(codes.NotFound, "organization ID: \"%v\" not found", orgId)
		}
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	imageData := bytes.Buffer{}

	for {
		req, err := srv.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			logger.Errorf("unexpected error during AddPhoto: %v", err)
			return status.Error(codes.Unknown, "unexpected error during AddPhoto")
		}

		chunk := req.GetPhoto()
		_, err = imageData.Write(chunk)
		if err != nil {
			logger.Errorf("unexpected error during AddPhoto: %v", err)
			return status.Error(codes.Unknown, "unexpected error during AddPhoto")
		}
	}

	s3handle, err := storage.NewS3Storage(config.S3OrganizationsLogosBucketName)
	if err != nil {
		logger.Errorf("unexpected error during AddPhoto: %v", err)
		return status.Error(codes.Unknown, "unexpected error during AddPhoto")
	}

	newLocation, err := s3handle.PutObject(imageData, orgRequestedID.String())
	if err != nil {
		logger.Errorf("unexpected error during AddPhoto: %v", err)
		return status.Error(codes.Unknown, "unexpected error during AddPhoto")
	}

	dbResult = s.DB.Model(&org).Update("logo", newLocation)
	if dbResult.Error != nil {
		logger.Errorf("error during updating organization with logo: %v", dbResult.Error)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	emptyResp := &emptypb.Empty{}
	err = srv.SendAndClose(emptyResp)
	if err != nil {
		logger.Errorf("unexpected error during AddPhoto: %v", err)
		return status.Error(codes.Unknown, "unexpected error during AddPhoto")
	}

	return nil
}

func (s *GRPCServer) DeletePhoto(_ context.Context, req *pb.OrganizationIdRequest) (*emptypb.Empty, error) {
	logger.Debugf("Delete photo request for the organization %s", req.Id)
	orgId := req.GetId()

	org := models.Organization{}

	orgRequestedID, err := uuid.Parse(orgId)
	if err != nil {
		logger.Errorf("error during parsing organization uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid organization UUID: \"%v\" ", orgId)
	}

	dbResult := s.DB.First(&org, "id = ?", orgRequestedID.String())
	if dbResult.Error != nil {
		logger.Errorf("error during getting organization: %v", dbResult.Error)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return nil, status.Errorf(codes.NotFound, "organization ID: \"%v\" not found", orgId)
		}
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	if org.Logo == "" {
		return nil, status.Errorf(codes.NotFound, "organization ID: \"%v\" has no logo", orgId)
	}

	s3handle, err := storage.NewS3Storage(config.S3OrganizationsLogosBucketName)
	if err != nil {
		logger.Errorf("error during deleting organization logo: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	err = s3handle.DeleteObject(orgId)
	if err != nil {
		logger.Errorf("error during deleting organization logo: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	dbResult = s.DB.Model(&org).Update("logo", nil)
	if dbResult.Error != nil {
		logger.Errorf("error during updating organization with logo: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	return &emptypb.Empty{}, nil
}

func (s *GRPCServer) GetPhoto(grpcCtx context.Context, req *pb.OrganizationIdRequest) (*pb.PreUrlResponse, error) {
	logger.Debugf("GetPhoto request for the organization %s", req.Id)
	orgId := req.GetId()

	org := models.Organization{}

	orgRequestedID, err := uuid.Parse(orgId)
	if err != nil {
		logger.Errorf("error during parsing organization uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid organization UUID: \"%v\" ", orgId)
	}

	dbResult := s.DB.First(&org, "id = ?", orgRequestedID.String())
	if dbResult.Error != nil {
		logger.Errorf("error during getting organization: %v", dbResult.Error)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return nil, status.Errorf(codes.NotFound, "organization ID: \"%v\" not found", orgId)
		}
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	if org.Logo == "" {
		return nil, status.Errorf(codes.NotFound, "organization ID: \"%v\" has no logo", orgId)
	}

	s3handle, err := storage.NewS3Storage(config.S3OrganizationsLogosBucketName)
	if err != nil {
		logger.Errorf("error during getting presigned url for organization logo: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	presignedURL, err := common.GetPresignedUrlWithMaybeReplacedHost(grpcCtx, s3handle, orgId)
	if err != nil {
		logger.Errorf("error during getting presigned url for organization logo: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	response := pb.PreUrlResponse{
		PresignedUrl: presignedURL,
	}

	return &response, nil
}

func (s *GRPCServer) SendInvitationSimple(ctx context.Context, req *pb.OrganizationInvitiationRequest) (*emptypb.Empty, error) {
	return s.SendInvitation(ctx, req)
}

func (s *GRPCServer) SendInvitation(ctx context.Context, req *pb.OrganizationInvitiationRequest) (*emptypb.Empty, error) {
	if req.OrganizationData == nil || req.AdminData == nil {
		logger.Errorf("missing OrganizationData or AdminData in body")
		return nil, status.Error(codes.InvalidArgument, "bad request")
	}

	if req.OrganizationData.Name == "" {
		logger.Errorf("missing OrganizationData.Name in body")
		return nil, status.Error(codes.InvalidArgument, "missing OrganizationData.Name in body")
	}

	transaction := func(tx *gorm.DB) error {
		logger.Debugf("Send invitation request for the organization named '%s'", req.OrganizationData.Name)
		authTokenData, authTokenDataPresent := grpcUtils.GetAuthTokenHeaderData(ctx)

		orgData := req.OrganizationData
		org := models.Organization{
			Name:                orgData.Name,
			Country:             orgData.Country,
			Location:            orgData.Location,
			Type:                orgData.Type,
			CellID:              orgData.CellId,
			RequestAccessReason: orgData.RequestAccessReason,
			Status:              "RGS",
			ModifiedAt: &sql.NullTime{
				Valid: false,
			},
			CreatedBy: orgData.CreatedBy,
		}
		if authTokenDataPresent {
			org.CreatedBy = authTokenData.UserID
		}

		err := orgService.CreateOrganizationWithStatusHistory(tx, &org)
		if err != nil {
			return err
		}

		defaultWorkspace := models.Workspace{
			Name:           config.DefaultWorkspaceName,
			OrganizationID: org.ID,
			CreatedBy:      orgData.CreatedBy,
		}
		if authTokenDataPresent {
			defaultWorkspace.CreatedBy = authTokenData.UserID
		}

		err = workspace.CreateWorkspace(tx, &defaultWorkspace)
		if err != nil {
			return err
		}

		adminUserData := req.AdminData
		if !grpcUtils.IsEmailValid(adminUserData.Email) {
			logger.Errorf("invalid user email: %v", adminUserData.Email)
			return status.Errorf(codes.InvalidArgument, "Invalid email: \"%v\" ", adminUserData.Email)
		}

		adminUser := models.User{
			FirstName:  adminUserData.FirstName,
			SecondName: adminUserData.SecondName,
			Email:      adminUserData.Email,
			ExternalId: adminUserData.ExternalId,
			Country:    adminUserData.Country,
			CreatedBy:  adminUserData.CreatedBy,
		}
		if authTokenDataPresent {
			adminUser.CreatedBy = authTokenData.UserID
		}

		nowTime := sql.NullTime{Valid: true, Time: time.Now()}
		if adminUserData.UserConsent != nil && *adminUserData.UserConsent != "" {
			adminUser.UserConsent = adminUserData.UserConsent
			adminUser.UserConsentAt = &nowTime
		}

		if adminUserData.TelemetryConsent != nil && *adminUserData.TelemetryConsent != "" {
			adminUser.TelemetryConsent = adminUserData.TelemetryConsent
			adminUser.TelemetryConsentAt = &nowTime
		}

		adminUserStatus := models.UserStatus{
			Status:         "RGS",
			OrganizationID: org.ID,
			Current:        true,
			CreatedBy:      adminUserData.CreatedBy,
		}
		if authTokenDataPresent {
			adminUserStatus.CreatedBy = authTokenData.UserID
		}

		err = user.CreateUser(ctx, tx, &adminUser, &adminUserStatus)
		if err != nil {
			return err
		}

		initUserAdminRolesOps := []*pb.UserRoleOperation{
			{Role: &pb.UserRole{
				Role:         "workspace_admin",
				ResourceType: "workspace",
				ResourceId:   defaultWorkspace.ID.String(),
			},
				Operation: "CREATE"},
			{Role: &pb.UserRole{
				Role:         "workspace_contributor",
				ResourceType: "workspace",
				ResourceId:   defaultWorkspace.ID.String(),
			},
				Operation: "CREATE"},
			{Role: &pb.UserRole{
				Role:         "organization_admin",
				ResourceType: "organization",
				ResourceId:   org.ID.String(),
			},
				Operation: "CREATE"},
		}

		alreadyAppliedRoleOps, err := user.ChangeUserRelationsByRoleOperations(adminUser.ID.String(), initUserAdminRolesOps)
		if err != nil {
			logger.Errorf("error during setting user roles: %v", err)
			user.RollbackRoleOps(alreadyAppliedRoleOps, adminUser.ID.String())
			return err
		}

		type InvitationFilling struct {
			InvitationLink   string
			OrganizationName string
			WorkspaceName    string
		}

		filling := InvitationFilling{
			InvitationLink:   config.InvitationLink,
			OrganizationName: org.Name,
			WorkspaceName:    defaultWorkspace.Name,
		}

		tmpl, err := template.New("invitation").Parse(config.OrganizationInvitationMailMessage)
		if err != nil {
			logger.Errorf("error during parsing invitation template: %v", err)
			user.RollbackRoleOps(alreadyAppliedRoleOps, adminUser.ID.String())
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		var invitationMessage bytes.Buffer
		err = tmpl.Execute(&invitationMessage, filling)
		if err != nil {
			logger.Errorf("error during executing invitation template: %v", err)
			user.RollbackRoleOps(alreadyAppliedRoleOps, adminUser.ID.String())
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		message := map[string]string{
			"subject":      config.OrganizationInvitationTopic,
			"to":           req.AdminData.Email,
			"from_address": config.InvitationFromAddress,
			"from_name":    config.InvitationFromName,
			"content":      "",
			"html_content": invitationMessage.String(),
		}

		jsonMsg, err := json.Marshal(message)
		if err != nil {
			logger.Errorf("error during marshalling invitation message: %v", err)
			user.RollbackRoleOps(alreadyAppliedRoleOps, adminUser.ID.String())
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		err = messaging.SendMessage(config.KafkaTopicPrefix+config.GetiNotificationTopic, jsonMsg)
		if err != nil {
			logger.Errorf("error during pushing invitation message to queue: %v", err)
			user.RollbackRoleOps(alreadyAppliedRoleOps, adminUser.ID.String())
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		return nil
	}

	err := s.DB.Transaction(transaction)
	if err != nil {
		logger.Errorf("failed DB transaction during organization '%s' invitation, rollback. %s",
			req.OrganizationData.Name, err)
		return nil, err
	}
	logger.Infof("Invitation for the organization '%s' has been sent", req.OrganizationData.Name)
	return &emptypb.Empty{}, nil
}
