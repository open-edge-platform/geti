// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package user

import (
	"context"
	"fmt"
	"strings"

	"account_service/app/config"
	"account_service/app/grpc/common"
	grpcUtils "account_service/app/grpc/utils"
	"account_service/app/models"
	"account_service/app/roles"

	"geti.com/account_service_grpc/pb"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/google/uuid"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"gorm.io/gorm"
)

func buildFindStatements(findRequest *pb.FindUserRequest, statementSession *gorm.DB) (*gorm.DB, error) {
	if findRequest.Name != "" {
		likePattern := fmt.Sprintf("%%%s%%", findRequest.Name)
		statementSession = statementSession.Where("first_name ILIKE ? OR second_name ILIKE ? OR LOWER(email) ILIKE ?", likePattern, likePattern, strings.ToLower(likePattern))
	}
	if findRequest.FirstName != "" {
		statementSession = statementSession.Where("first_name LIKE ?", fmt.Sprintf("%%%s%%", findRequest.FirstName))
	}
	if findRequest.SecondName != "" {
		statementSession = statementSession.Where("second_name LIKE ?", fmt.Sprintf("%%%s%%", findRequest.SecondName))
	}
	if findRequest.Email != "" {
		statementSession = statementSession.Where("LOWER(email) LIKE ?", fmt.Sprintf("%%%s%%", strings.ToLower(findRequest.Email)))
	}
	if findRequest.ExternalId != "" {
		statementSession = statementSession.Where("external_id = ?", findRequest.ExternalId)
	}
	if findRequest.Country != "" {
		statementSession = statementSession.Where("country = ?", findRequest.Country)
	}

	//Join with UserStatus table
	statementSession = statementSession.Joins("left join user_statuses on users.id = user_statuses.user_id")
	statementSession = statementSession.Where("user_statuses.current = ?", "TRUE")
	statementSession = statementSession.Where("user_statuses.status <> ?", "DEL")
	if findRequest.Status != "" {
		statementSession = statementSession.Where("user_statuses.status = ?", findRequest.Status)
	}

	if findRequest.OrganizationId != "" {
		parsedOrganizationUUID, err := uuid.Parse(findRequest.OrganizationId)
		if err != nil {
			logger.Errorf("error during parsing organization's UUID: %v", err)
			return statementSession, status.Error(codes.InvalidArgument, "malformed organization's UUID")
		}
		statementSession = statementSession.Where("user_statuses.organization_id = ?", parsedOrganizationUUID.String())
	}

	if findRequest.LastSuccessfulLoginFrom != nil && findRequest.LastSuccessfulLoginTo != nil {
		statementSession = statementSession.Where(
			"last_successful_login BETWEEN ? AND ?", findRequest.LastSuccessfulLoginFrom.AsTime(), findRequest.LastSuccessfulLoginTo.AsTime(),
		)
	} else if findRequest.LastSuccessfulLoginFrom != nil {
		statementSession = statementSession.Where("last_successful_login > ?", findRequest.LastSuccessfulLoginFrom.AsTime())
	} else if findRequest.LastSuccessfulLoginTo != nil {
		statementSession = statementSession.Where("last_successful_login < ?", findRequest.LastSuccessfulLoginTo.AsTime())
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

	if findRequest.ModifiedAtFrom != nil && findRequest.ModifiedAtTo != nil {
		statementSession = statementSession.Where(
			"modified_at BETWEEN ? AND ?", findRequest.ModifiedAtFrom.AsTime(), findRequest.ModifiedAtTo.AsTime(),
		)
	} else if findRequest.ModifiedAtFrom != nil {
		statementSession = statementSession.Where("modified_at > ?", findRequest.ModifiedAtFrom.AsTime())
	} else if findRequest.ModifiedAtTo != nil {
		statementSession = statementSession.Where("modified_at < ?", findRequest.ModifiedAtTo.AsTime())
	}

	if findRequest.CreatedBy != "" {
		statementSession = statementSession.Where("created_by = ?", findRequest.CreatedBy)
	}

	if findRequest.ModifiedBy != "" {
		statementSession = statementSession.Where("modified_by = ?", findRequest.ModifiedBy)
	}

	return statementSession, nil
}

func buildPaginationStatements(findRequest *pb.FindUserRequest, statementSession *gorm.DB) *gorm.DB {
	if findRequest.Skip > 0 {
		statementSession = statementSession.Offset(int(findRequest.Skip))
	}

	if findRequest.Limit > 0 {
		statementSession = statementSession.Limit(int(findRequest.Limit))
	}

	return statementSession
}

func buildOrderStatement(findRequest *pb.FindUserRequest, statementSession *gorm.DB) (*gorm.DB, error) {
	logger.Debug("Checking sort conditions")
	if findRequest.SortBy != "" && findRequest.SortDirection != "" {
		var orderQuery string
		var err error
		if findRequest.SortBy == "status" {
			orderQuery = fmt.Sprintf("%v %v", "user_statuses.status", findRequest.SortDirection)
		} else {
			orderQuery, err = common.CreateOrderQuery(models.User{}, findRequest.SortBy, findRequest.SortDirection)
			if err != nil {
				return nil, err
			}
		}
		statementSession = statementSession.Order(orderQuery)
	}
	return statementSession, nil
}

type UserIDToUserRolesMap map[string][]*pb.UserRole

func retrieveRolesForUsers(users []models.User) (UserIDToUserRolesMap, error) {
	var userIds []string
	for _, user := range users {
		userIds = append(userIds, user.ID.String())
	}

	logger.Debug("Starting role retrieval")
	userRolesMap := make(UserIDToUserRolesMap)
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize client: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	var userRelationships []*v1.Relationship
	for _, userId := range userIds {
		logger.Debugf("Retrieving roles for user with id %v", userId)
		userRelationships, err = rolesMgr.GetUserAllRelationships(userId)
		if err != nil {
			logger.Errorf("error during get user roles: %v", err)
			return nil, status.Errorf(codes.Unknown, "unexpected error")
		}
		logger.Debugf("Retrieved relationships: %v", userRelationships)

		userRoles := common.RelationshipsToUserRoles(userRelationships)

		userRolesMap[userId] = userRoles
	}

	return userRolesMap, nil

}

func filterUsersByRole(findRequest *pb.FindUserRequest, users []models.User, userRolesMap UserIDToUserRolesMap) []models.User {
	// Filters out USERS (not roles) based on the resource type and role passed in the find request
	logger.Debug("Filtering users based on the role find request criteria")
	var filteredUsers []models.User
	for _, user := range users {
		userRoles, exists := userRolesMap[user.ID.String()]
		if exists && common.HasRole(userRoles, findRequest.Role, findRequest.ResourceType, findRequest.ResourceId) {
			filteredUsers = append(filteredUsers, user)
		}
	}
	return filteredUsers
}

type UserIDToUserStatusMap map[uuid.UUID]models.UserStatus

func mapUserStatuses(userStatuses []models.UserStatus) UserIDToUserStatusMap {
	userStatusesMap := make(map[uuid.UUID]models.UserStatus, len(userStatuses))
	for _, userStatus := range userStatuses {
		userStatusesMap[userStatus.UserID] = userStatus
	}
	return userStatusesMap
}

func usersIDs(users []models.User) []uuid.UUID {
	ids := make([]uuid.UUID, len(users))
	for i, user := range users {
		ids[i] = user.ID
	}
	return ids
}

func (s *GRPCServer) retrieveUserStatuses(ctx context.Context, organizationID string, users []models.User) (UserIDToUserStatusMap, error) {
	var userStatusesMap UserIDToUserStatusMap

	if organizationID != "" {
		var userStatuses []models.UserStatus

		// get user statuses and org statuses for previously found users
		statusSession := s.DB.WithContext(ctx)

		// filter user statuses based on organization_id if it's present in the request
		statusSession = statusSession.Where("organization_id = ?", organizationID)
		statusSession = statusSession.Where("user_id IN ?", usersIDs(users))
		statusSession = statusSession.Where("current = ?", "TRUE")
		dbResult := statusSession.Preload("Organization").Find(&userStatuses)
		if dbResult.Error != nil {
			logger.Errorf("error during users statuses find: %v", dbResult.Error)
			return nil, status.Errorf(codes.Unknown, "unexpected error")
		}

		userStatusesMap = mapUserStatuses(userStatuses)
	}
	return userStatusesMap, nil
}

func countMatched(statementSession *gorm.DB) (int32, error) {
	var totalMatchedCount int64
	dbResult := statementSession.Count(&totalMatchedCount)
	if dbResult.Error != nil {
		logger.Errorf("error during user total matched count: %v", dbResult.Error)
		return 0, status.Errorf(codes.Unknown, "unexpected error")
	}
	return int32(totalMatchedCount), nil
}

func (s *GRPCServer) countAll(ctx context.Context, organizationID string) (int32, error) {
	if organizationID != "" {
		var userStatuses []models.UserStatus
		var totalCount64 int64
		statusSession := s.DB.WithContext(ctx).Model(&userStatuses)
		statusSession = statusSession.Where("organization_id = ? AND current = ? AND status <> ?", organizationID, "TRUE", "DEL")
		dbResult := statusSession.Count(&totalCount64)
		if dbResult.Error != nil {
			logger.Errorf("error during users statuses find: %v", dbResult.Error)
			return 0, status.Errorf(codes.Unknown, "unexpected error")
		}
		return int32(totalCount64), nil
	}
	return common.CountAll(s.DB, models.User{})
}

type UserRolesFilter struct {
	OrganizationID string
	ResourceTypes  []string
	ResourceId     string
}

func filterUserRoles(ctx context.Context, userData *pb.UserData, userRolesMap UserIDToUserRolesMap, filter UserRolesFilter) error {
	if userRoles, exists := userRolesMap[userData.Id]; exists {
		var filteredRoles []*pb.UserRole

		for _, role := range userRoles {
			logger.Debugf("Checking role %v", role)

			if (len(filter.ResourceTypes) == 0 || grpcUtils.Contains(filter.ResourceTypes, "organization")) && role.ResourceType == "organization" && role.ResourceId == filter.OrganizationID {
				// default case where only roles for current organization are returned
				filteredRoles = append(filteredRoles, role)
			} else if grpcUtils.Contains(filter.ResourceTypes, role.ResourceType) {
				if filter.ResourceId != "" { // resource type and id provided
					if filter.ResourceId == role.ResourceId {
						filteredRoles = append(filteredRoles, role)
					}
				} else { // resource type provided, missing id
					filteredRoles = append(filteredRoles, role)
				}
			}
		}

		authTokenData, isAuthTokenPresent := grpcUtils.GetAuthTokenHeaderData(ctx)

		if isAuthTokenPresent {
			logger.Debug("auth token present, filtering by permissions...")
			var err error
			filteredRoles, err = common.FilterRolesByCurrentUserPermissions(authTokenData.UserID, filteredRoles)
			if err != nil {
				logger.Errorf("error during filtering roles: %v", err)
				return status.Errorf(codes.Unknown, "unexpected error")
			}
		} else {
			logger.Debug("auth token not present, filtering by permissions skipped!")
		}

		logger.Debugf("Returning filtered roles %v for user %v", filteredRoles, userData.Id)
		userData.Roles = filteredRoles
	}
	return nil
}

func userModelToUserData(ctx context.Context,
	rolesFilter UserRolesFilter,
	user models.User,
	userStatus models.UserStatus,
	userRolesMap UserIDToUserRolesMap) (*pb.UserData, error) {

	logger.Debugf("Preparing user data for user %v", user)

	userData := &pb.UserData{
		Id:                     user.ID.String(),
		FirstName:              user.FirstName,
		SecondName:             user.SecondName,
		Email:                  user.Email,
		ExternalId:             user.ExternalId,
		Status:                 userStatus.Status,
		OrganizationId:         userStatus.OrganizationID.String(),
		OrganizationStatus:     userStatus.Organization.Status,
		LastSuccessfulLogin:    common.SqlTimeToTimestamp(user.LastSuccessfulLogin),
		CurrentSuccessfulLogin: common.SqlTimeToTimestamp(user.CurrentSuccessfulLogin),
	}

	err := filterUserRoles(ctx, userData, userRolesMap, rolesFilter)
	if err != nil {
		return nil, err
	}
	return userData, nil
}

func (s *GRPCServer) Find(ctx context.Context, findRequest *pb.FindUserRequest) (*pb.ListUsersResponse, error) {
	logger.Debugf("Find users request received, content: %v", findRequest)

	if findRequest.ResourceId != "" && len(findRequest.ResourceType) > 1 {
		return nil, status.Error(codes.InvalidArgument,
			"Invalid request - can't request more than 1 resource type while resource id is passed.")
	}

	var users []models.User
	statementSession := s.DB.WithContext(ctx)
	statementSession = statementSession.Model(&users)

	statementSession, err := buildFindStatements(findRequest, statementSession)
	if err != nil {
		return nil, err
	}

	response := pb.ListUsersResponse{}

	response.TotalMatchedCount, err = countMatched(statementSession)
	if err != nil {
		return nil, err
	}

	statementSession = buildPaginationStatements(findRequest, statementSession)

	statementSession, err = buildOrderStatement(findRequest, statementSession)
	if err != nil {
		return nil, err
	}

	dbResult := statementSession.Find(&users)
	if dbResult.Error != nil {
		logger.Errorf("error during user find: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	userRolesMap, err := retrieveRolesForUsers(users)
	if err != nil {
		return nil, err
	}

	if len(findRequest.ResourceType) > 0 || findRequest.Role != "" || findRequest.ResourceId != "" {
		users = filterUsersByRole(findRequest, users, userRolesMap)
		response.TotalMatchedCount = int32(len(users))
	}

	userStatusesMap, err := s.retrieveUserStatuses(ctx, findRequest.OrganizationId, users)
	if err != nil {
		return nil, err
	}

	for _, userModel := range users {
		var userStatus models.UserStatus
		var ok bool

		if userStatusesMap != nil {
			userStatus, ok = userStatusesMap[userModel.ID]
			if !ok {
				continue
			}
		}

		rolesFilter := UserRolesFilter{
			OrganizationID: findRequest.OrganizationId,
			ResourceTypes:  findRequest.ResourceType,
			ResourceId:     findRequest.ResourceId,
		}
		userData, err := userModelToUserData(ctx, rolesFilter, userModel, userStatus, userRolesMap)
		if err != nil {
			return nil, err
		}
		response.Users = append(response.Users, userData)
	}

	totalCount, err := s.countAll(ctx, findRequest.OrganizationId)
	if err != nil {
		return nil, err
	}

	response.TotalCount = totalCount
	const DefaultLimit = 10
	nextPageFields := common.CalculateNextPage(response.TotalCount, findRequest.Skip, func() int32 {
		if findRequest.Limit < DefaultLimit {
			return DefaultLimit
		}
		return findRequest.Limit
	}())

	nextPage := pb.ListUsersResponse_NextPage{
		Skip:  nextPageFields.Skip,
		Limit: nextPageFields.Limit,
	}

	response.NextPage = &nextPage

	return &response, nil
}
