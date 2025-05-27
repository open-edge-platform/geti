// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package user

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"html/template"
	"io"
	"net/url"
	"slices"
	"strings"
	"time"

	"account_service/app/common/utils"
	"account_service/app/config"
	"account_service/app/fsm"
	"account_service/app/grpc/common"
	grpcUtils "account_service/app/grpc/utils"
	"account_service/app/messaging"
	"account_service/app/models"
	"account_service/app/repository"
	"account_service/app/roles"
	roleService "account_service/app/services/role"
	service "account_service/app/services/user"
	serviceUtils "account_service/app/services/utils"
	workspaceService "account_service/app/services/workspace"
	"account_service/app/storage"

	"geti.com/account_service_grpc/pb"

	internalErrors "account_service/app/errors"

	cs "geti.com/credit_system"
	authzed "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/google/uuid"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
)

type GRPCServer struct {
	pb.UnimplementedUserServer
	DB               *gorm.DB
	WorkspaceService *workspaceService.Service
	Service          service.UserService
}

var logger = utils.InitializeLogger()

func (s *GRPCServer) GetUsers(ctx context.Context, req *pb.GetUsersRequest) (*pb.ListGetUsersResponse, error) {
	//Checks request fields in grpc package to return grpc specific codes
	if req.SortDirection != "asc" && req.SortDirection != "desc" && req.SortDirection != "" {
		logger.Errorf("Wrong sort direction: %v", internalErrors.NewInvalidReuestError("Wrong sort direction"))
		return nil, status.Errorf(codes.InvalidArgument, "Wrong sort direction")
	}

	users, totalMatchedCount, err := s.Service.GetUsers(ctx, req)
	logger.Infof("Found users: %v", users)

	users_data := &pb.ListGetUsersResponse{}
	for _, user := range users {
		userPb, err := UserToResponsePB(user)
		if err != nil {
			return nil, err
		}
		users_data.Users = append(users_data.Users, userPb)
	}

	users_data.TotalMatchedCount = int32(totalMatchedCount)

	nextPageFields := common.CalculateNextPage(users_data.TotalMatchedCount, req.Skip, req.Limit)
	users_data.NextPage = &pb.ListGetUsersResponse_NextPage{
		Skip:  nextPageFields.Skip,
		Limit: nextPageFields.Limit,
	}

	if err != nil {
		logger.Errorf("error getting users: %v", err)
		return nil, status.Errorf(codes.Internal, "unexpected error")
	}

	return users_data, nil
}

func UserToResponsePB(user models.User) (*pb.UserResponse, error) {
	userData := &pb.UserResponse{
		Id:                     user.ID.String(),
		FirstName:              user.FirstName,
		SecondName:             user.SecondName,
		Email:                  user.Email,
		ExternalId:             user.ExternalId,
		Country:                user.Country,
		PhotoLocation:          user.PhotoLocation,
		RegistrationToken:      user.RegistrationToken,
		CreatedAt:              timestamppb.New(user.CreatedAt),
		ModifiedAt:             common.SqlTimeToTimestamp(user.ModifiedAt),
		LastSuccessfulLogin:    common.SqlTimeToTimestamp(user.LastSuccessfulLogin),
		CurrentSuccessfulLogin: common.SqlTimeToTimestamp(user.CurrentSuccessfulLogin),
		CreatedBy:              user.CreatedBy,
		ModifiedBy:             user.ModifiedBy,
		TelemetryConsent:       user.TelemetryConsent,
		TelemetryConsentAt:     common.SqlTimeToTimestamp(user.TelemetryConsentAt),
		UserConsent:            user.UserConsent,
		UserConsentAt:          common.SqlTimeToTimestamp(user.UserConsentAt),
	}

	logger.Infof("PB user: %v", userData)
	return userData, nil
}

func UserToPb(user models.User, userStatus models.UserStatus, presignedURL string) *pb.UserData {
	userData := &pb.UserData{
		Id:         user.ID.String(),
		FirstName:  user.FirstName,
		SecondName: user.SecondName,
		Email:      user.Email,
		ExternalId: user.ExternalId,
		Country:    user.Country,
		// Need to convert time.Time to timestamppb.Timestamp
		CreatedAt:              timestamppb.New(user.CreatedAt),
		ModifiedAt:             common.SqlTimeToTimestamp(user.ModifiedAt),
		LastSuccessfulLogin:    common.SqlTimeToTimestamp(user.LastSuccessfulLogin),
		CurrentSuccessfulLogin: common.SqlTimeToTimestamp(user.CurrentSuccessfulLogin),
		CreatedBy:              user.CreatedBy,
		ModifiedBy:             user.ModifiedBy,
		Roles:                  nil, // Done explicitly in functions that return roles
		TelemetryConsent:       user.TelemetryConsent,
		TelemetryConsentAt:     common.SqlTimeToTimestamp(user.TelemetryConsentAt),
		UserConsent:            user.UserConsent,
		UserConsentAt:          common.SqlTimeToTimestamp(user.UserConsentAt),
		PresignedUrl:           presignedURL,
	}

	// Only include the user status if it's available
	if userStatus.Status != "" {
		userData.Status = userStatus.Status
		userData.OrganizationId = userStatus.OrganizationID.String()
		userData.OrganizationStatus = userStatus.Organization.Status
	}

	return userData
}

func (s *GRPCServer) userMustExistInDB(userID string) error {
	user := models.User{}

	parsedUserUUID, err := uuid.Parse(userID)
	if err != nil {
		logger.Errorf("error during parsing user uuid: %v", err)
		return status.Errorf(codes.InvalidArgument, "invalid user UUID: \"%v\" ", parsedUserUUID.String())
	}
	var count int64
	dbResult := s.DB.Model(&user).Where("id = ?", parsedUserUUID.String()).Count(&count)
	if dbResult.Error != nil {
		logger.Errorf("error during counting user: %v", dbResult.Error)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return status.Errorf(codes.NotFound, "user ID: \"%v\" not found", parsedUserUUID.String())
		}
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	if count == 0 {
		return status.Errorf(codes.NotFound, "user ID: \"%v\" not found", parsedUserUUID.String())
	}
	return nil
}

func GetUserFromDBByID(tx *gorm.DB, userID string) (*models.User, error) {
	user := models.User{}

	parsedUserUUID, err := uuid.Parse(userID)
	if err != nil {
		logger.Errorf("error during parsing user uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid user UUID: \"%v\" ", userID)
	}

	dbResult := tx.First(&user, "id = ?", parsedUserUUID.String())
	if dbResult.Error != nil {
		logger.Errorf("error during getting user: %v", dbResult.Error)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return nil, status.Errorf(codes.NotFound, "user ID: \"%v\" not found", userID)
		}
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	return &user, nil
}

func CountUsersByStatus(tx *gorm.DB, status string) (map[string]int64, error) {
	var internalUsersCount int64
	var externalUsersCount int64

	// Count internal users (email contains "intel" and given status)
	internalResult := tx.Model(&models.User{}).
		Select("COUNT(DISTINCT users.id)").
		Joins("JOIN user_statuses ON users.id = user_statuses.user_id").
		Where("user_statuses.status = ? AND user_statuses.current = ?", status, true).
		Where("LOWER(users.email) LIKE ?", "%@intel.%").
		Count(&internalUsersCount)
	if internalResult.Error != nil {
		logger.Errorf("error during counting internal users: %v", internalResult.Error)
		return nil, internalResult.Error
	}

	// Count external users (email does not contain "intel" and given status)
	externalResult := tx.Model(&models.User{}).
		Select("COUNT(DISTINCT users.id)").
		Joins("JOIN user_statuses ON users.id = user_statuses.user_id").
		Where("user_statuses.status = ? AND user_statuses.current = ?", status, true).
		Where("LOWER(users.email) NOT LIKE ?", "%@intel.%").
		Count(&externalUsersCount)
	if externalResult.Error != nil {
		logger.Errorf("error during counting external users: %v", externalResult.Error)
		return nil, externalResult.Error
	}

	return map[string]int64{
		"internal": internalUsersCount,
		"external": externalUsersCount,
	}, nil
}

func getUsersLimit(ctx context.Context, userStatus *models.UserStatus) (int64, error) {
	if config.FeatureFlagOrgQuotas {
		quotasClient, err := cs.InitializeQuotasClient()
		if err != nil {
			errorMsg := fmt.Errorf("failed to initialize credit system gRPC connection %v", err)
			logger.Error(errorMsg)
			return -1, errorMsg
		}

		usersQuota, err := quotasClient.GetUsersQuota(ctx, userStatus.OrganizationID.String())
		if !quotasClient.CloseConnection() {
			logger.Error("failed to close gRPC connection to the credit system")
		}
		if err != nil {
			errorMsg := fmt.Errorf("failed to get users quota information %v", err)
			logger.Error(errorMsg)
			return -1, errorMsg
		}

		logger.Debugf("received Users Quota for the organization %s: service %s, name '%s', type '%s', limit %d", usersQuota.OrganizationId, usersQuota.ServiceName, usersQuota.QuotaName, usersQuota.QuotaType, usersQuota.Limit)
		return usersQuota.Limit, nil

	}
	return int64(config.UsersPerOrgLimit), nil // default set by impt-configuration cm
}

func CreateUser(ctx context.Context, tx *gorm.DB, user *models.User, userStatus *models.UserStatus) error {
	err := tx.Exec(`LOCK TABLE user_statuses IN ACCESS EXCLUSIVE MODE`).Error
	if err != nil {
		logger.Errorf("failed to lock table user_statuses: %v", err)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	var users []models.User
	var matchingGlobalActiveUsersCount int64 = 0
	var matchingActiveUsersInParticularOrganizationCount int64 = 0

	loweredUserEmail := strings.ToLower(user.Email)

	countUsersQuerySession := tx.Model(&users).Joins("left join user_statuses on users.id = user_statuses.user_id").
		Where("LOWER(users.email) = ?", loweredUserEmail).
		Where("user_statuses.current = ?", "TRUE").
		Where("user_statuses.status <> ?", "DEL").
		Count(&matchingGlobalActiveUsersCount)
	if countUsersQuerySession.Error != nil {
		logger.Errorf("error during counting active users in global context with email: \"%v\" , db error: %v",
			loweredUserEmail,
			countUsersQuerySession.Error)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	countUsersQuerySession.Where("user_statuses.organization_id = ?", userStatus.OrganizationID.String())
	dbResult := countUsersQuerySession.Count(&matchingActiveUsersInParticularOrganizationCount)
	if dbResult.Error != nil {
		logger.Errorf("error during counting active users in particular organization: \"%v\" "+
			"with email: \"%v\", db error : %v",
			userStatus.OrganizationID.String(),
			loweredUserEmail,
			countUsersQuerySession.Error)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	if matchingActiveUsersInParticularOrganizationCount > 0 {
		logger.Errorf("user with email '%s' already exists in organization %s",
			user.Email, userStatus.OrganizationID.String())
		return status.Errorf(codes.AlreadyExists, "user with email \"%v\" in organization \"%v\" "+
			"already exists", user.Email, userStatus.OrganizationID.String())
	}

	var orgUsersCount int64
	modelStatus := models.UserStatus{}
	dbResult = tx.Model(&modelStatus).
		Where("organization_id = ? AND status <> ? AND current = ?", userStatus.OrganizationID.String(), "DEL", "TRUE").
		Count(&orgUsersCount)
	if dbResult.Error != nil {
		logger.Errorf("error during counting organization's user statuses: %v", dbResult.Error)
		return status.Errorf(codes.Unknown, "unexpected error")
	}
	if orgUsersCount >= 1 { // workaround, when init org & user are being created - there's no credit subscription yet
		usersLimit, err := getUsersLimit(ctx, userStatus)
		if err != nil {
			return status.Errorf(codes.Unknown, "unexpected error")
		}
		if usersLimit > -1 {
			if orgUsersCount >= usersLimit {
				logger.Errorf("couldn't create a new user with email '%s': the organization %s has reached "+
					"the allowed number of users limit (%d)", user.Email, userStatus.OrganizationID.String(), usersLimit)

				return status.Errorf(codes.FailedPrecondition,
					"the organization has reached the allowed number of users limit: \"%v\"", usersLimit)
			}
		}
	}

	if matchingGlobalActiveUsersCount == 0 {
		result := tx.Model(&models.User{}).Create(&user)
		if result.Error != nil {
			logger.Errorf("error during user Create: %v", result.Error)
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		// Reload the user object from the database to get the actual creation timestamp
		result = tx.First(&user, user.ID)
		if result.Error != nil {
			logger.Errorf("error during user Reload: %v", result.Error)
			return status.Errorf(codes.Unknown, "unexpected error")
		}
	} else {
		dbResult := tx.Model(&users).Joins("left join user_statuses on users.id = user_statuses.user_id").
			Where("LOWER(users.email) = ?", loweredUserEmail).
			Where("user_statuses.current = ?", "TRUE").
			Where("user_statuses.status <> ?", "DEL").
			First(&user)
		if dbResult.Error != nil {
			logger.Errorf("error during fetching global user: %v", dbResult.Error)
			return status.Errorf(codes.Unknown, "unexpected error")
		}
	}

	userStatus.UserID = user.ID

	result := tx.Create(&userStatus)
	if result.Error != nil {
		logger.Errorf("error during user status Create: %v", result.Error)
		return status.Errorf(codes.Unknown, "unexpected error")
	}
	logger.Infof("User %s has been successfully created, user status: %s, organization: %s",
		userStatus.UserID.String(), userStatus.Status, userStatus.OrganizationID.String())

	return nil
}

func (s *GRPCServer) Create(ctx context.Context, data *pb.UserData) (*pb.UserData, error) {
	logger.Infof("request user Create")

	if !grpcUtils.IsEmailValid(data.Email) {
		logger.Errorf("invalid user email: %v", data.Email)
		return nil, status.Errorf(codes.InvalidArgument, "Invalid email: \"%v\" ", data.Email)
	}

	user := models.User{
		FirstName:        data.FirstName,
		SecondName:       data.SecondName,
		Email:            strings.ToLower(data.Email),
		ExternalId:       data.ExternalId,
		Country:          data.Country,
		UserConsent:      data.UserConsent,
		TelemetryConsent: data.TelemetryConsent,
		ModifiedAt: &sql.NullTime{
			Valid: false,
		},
		CreatedBy: data.CreatedBy,
	}

	authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
	if ok {
		user.CreatedBy = authTokenData.UserID
	}

	nowTime := sql.NullTime{Valid: true, Time: time.Now()}
	if data.UserConsent != nil && *data.UserConsent != "" {
		user.UserConsent = data.UserConsent
		user.UserConsentAt = &nowTime
	}

	if data.TelemetryConsent != nil && *data.TelemetryConsent != "" {
		user.TelemetryConsent = data.TelemetryConsent
		user.TelemetryConsentAt = &nowTime
	}

	orgId, err := uuid.Parse(data.OrganizationId)
	if err != nil {
		logger.Errorf("error parsing organization id: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid organization id")
	}

	userStatus := models.UserStatus{
		Status:         data.Status,
		OrganizationID: orgId,
		Current:        true,
	}

	transaction := func(tx *gorm.DB) error {
		return CreateUser(ctx, tx, &user, &userStatus)
	}

	err = s.DB.Transaction(transaction)
	if err != nil {
		return nil, err
	}

	// Fetch the latest organization status history for the organization
	var orgStatus models.OrganizationStatusHistory
	result := s.DB.Where("organization_id = ?", orgId).Order("created_at desc").First(&orgStatus)
	if result.Error != nil {
		logger.Errorf("error fetching organization status: %v", result.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error fetching organization status")
	}

	pbUser := UserToPb(user, userStatus, "")
	pbUser.OrganizationStatus = orgStatus.Status

	return pbUser, nil
}

func (s *GRPCServer) GetUserProfile(ctx context.Context, _ *emptypb.Empty) (*pb.UserProfileData, error) {
	authHeaderData, ok := grpcUtils.GetExternalTokenHeaderData(ctx)
	if !ok {
		return nil, status.Errorf(codes.InvalidArgument, "Invalid request")
	}
	logger.Debugf("Get profile request received. Incoming token data: %v", authHeaderData)

	var userData models.User

	dbResult := s.DB.Model(&userData).Joins("left join user_statuses on users.id = user_statuses.user_id").
		Where("user_statuses.status <> ?", "DEL").
		Where("user_statuses.current = ?", "TRUE").
		Where("LOWER(users.email) = ?", strings.ToLower(authHeaderData.Email)).
		First(&userData)
	if dbResult.Error != nil {
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			logger.Errorf("Failed get user profile request: user with email %s not found", authHeaderData.Email)
			return nil, status.Error(codes.NotFound, "User not found")
		}
		logger.Errorf("Database error: %v", dbResult.Error)
		return nil, status.Error(codes.Unknown, "unexpected error")
	}
	logger.Debugf("Found user %v", userData)

	userProfileResponse := pb.UserProfileData{
		UserConsent:        userData.UserConsent,
		UserConsentAt:      common.SqlTimeToTimestamp(userData.UserConsentAt),
		TelemetryConsent:   userData.TelemetryConsent,
		TelemetryConsentAt: common.SqlTimeToTimestamp(userData.TelemetryConsentAt),
	}

	var userStatuses []models.UserStatus
	res := s.DB.
		Preload("Organization").
		Where("user_id = ? AND current = ? AND status <> ?", userData.ID, "TRUE", "DEL").Find(&userStatuses)
	if res.Error != nil {
		logger.Errorf("Error fetching multiple user statuses during get user profile: %v", res.Error)
		return nil, status.Error(codes.Unknown, "unexpected error")
	}

	var userOrgs []*pb.OrganizationExtended
	for _, userStatus := range userStatuses {
		userOrgs = append(userOrgs, &pb.OrganizationExtended{
			OrganizationName:      userStatus.Organization.Name,
			UserStatus:            userStatus.Status,
			OrganizationStatus:    userStatus.Organization.Status,
			OrganizationId:        userStatus.Organization.ID.String(),
			OrganizationCreatedAt: timestamppb.New(userStatus.Organization.CreatedAt),
		})
	}

	userProfileResponse.Organizations = userOrgs

	return &userProfileResponse, nil

}

func (s *GRPCServer) GetActiveUser(ctx context.Context, req *pb.UserIdRequest) (*pb.ActiveUserData, error) {
	logger.Debug("get active user request")
	authHeaderData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)

	if ok {
		req.UserId = authHeaderData.UserID
	}

	user, err := s.GetById(ctx, req)
	if err != nil {
		return nil, err
	}

	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize client: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}
	userRelationships, err := rolesMgr.GetUserAllRelationshipsByOrganization(req.OrganizationId, user.Id)
	if err != nil {
		logger.Errorf("unable to get user relationships: %v", err)
		return nil, err
	}
	var userRoles []*pb.UserRole
	for _, relationship := range userRelationships {
		userRoles = append(userRoles, &pb.UserRole{
			Role:         relationship.Relation,
			ResourceType: relationship.Resource.ObjectType,
			ResourceId:   relationship.Resource.ObjectId,
		})
	}
	activeUserResponse := pb.ActiveUserData{
		Id:                     user.Id,
		FirstName:              user.FirstName,
		SecondName:             user.SecondName,
		Email:                  user.Email,
		Status:                 user.Status,
		OrganizationId:         user.OrganizationId,
		OrganizationStatus:     user.OrganizationStatus,
		Roles:                  userRoles,
		LastSuccessfulLogin:    user.LastSuccessfulLogin,
		CurrentSuccessfulLogin: user.CurrentSuccessfulLogin,
		TelemetryConsent:       user.TelemetryConsent,
		UserConsent:            user.UserConsent,
	}
	return &activeUserResponse, nil
}

func (s *GRPCServer) GetById(ctx context.Context, req *pb.UserIdRequest) (*pb.UserData, error) {
	userStatus := models.UserStatus{}

	user, err := GetUserFromDBByID(s.DB, req.UserId)
	if err != nil {
		return nil, err
	}

	dbResult := s.DB.Where("user_id = ? AND organization_id = ? AND current = ?",
		user.ID.String(), req.OrganizationId, "TRUE").First(&userStatus)
	if dbResult.Error != nil {
		logger.Errorf("error during getting user status: %v", dbResult.Error)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return nil, status.Errorf(codes.NotFound, "status for user ID: \"%v\" not found", req.UserId)
		}
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	userLogoPresignedURL := ""
	GetPhotoRequest := pb.UserIdRequest{
		UserId:         user.ID.String(),
		OrganizationId: req.OrganizationId,
	}
	preURLResponse, err := s.GetPhoto(ctx, &GetPhotoRequest)
	if err != nil {
		// only log, user may not have photo
		logger.Debugf("error getting photo for: %v, err: %v", user.ID.String(), err)
	} else {
		userLogoPresignedURL = preURLResponse.PresignedUrl
	}

	returnData := UserToPb(*user, userStatus, userLogoPresignedURL)
	returnData.LastLogoutDate = common.SqlTimeToTimestamp(user.LastLogoutDate)

	return returnData, nil
}

func (s *GRPCServer) GetByExternalId(_ context.Context, req *pb.UserExtIdRequest) (*pb.UserData, error) {
	logger.Debugf("get user by external id request, external ID: %s", req.Id)
	user := models.User{}

	unescapedExternalID, err := url.QueryUnescape(req.Id)
	if err != nil {
		logger.Errorf("error during get user request: invalid external ID %s", req.Id)
		return nil, status.Errorf(codes.InvalidArgument, "invalid format of external ID")
	}

	dbResult := s.DB.Model(&user).Joins("left join user_statuses on users.id = user_statuses.user_id").
		Where("user_statuses.status <> ?", "DEL").
		Where("user_statuses.current = ?", "TRUE").
		Where("users.external_id = ?", unescapedExternalID).
		First(&user)
	if dbResult.Error != nil {
		logger.Errorf("error during getting user: %v", dbResult.Error)
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return nil, status.Errorf(codes.NotFound, "user with External ID: \"%v\" not found", unescapedExternalID)
		}
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	return s.addOrganizationIdsToResponse(user)
}

func (s *GRPCServer) addOrganizationIdsToResponse(user models.User) (*pb.UserData, error) {
	var userStatuses []models.UserStatus
	res := s.DB.
		Preload("Organization").
		Where("user_id = ? AND current = ? AND status = ?", user.ID, "TRUE", "ACT").Find(&userStatuses)
	if res.Error != nil {
		logger.Errorf("Error fetching multiple user statuses during get user profile: %v", res.Error)
		return nil, status.Error(codes.Unknown, "unexpected error")
	}

	var returnData = UserToPb(user, models.UserStatus{}, "") // populate response without user status
	var orgIds []string
	for _, returnedStatus := range userStatuses {
		orgIds = append(orgIds, returnedStatus.OrganizationID.String())
	}
	returnData.OrganizationId = strings.Join(orgIds, ",")
	returnData.LastLogoutDate = common.SqlTimeToTimestamp(user.LastLogoutDate)

	return returnData, nil
}

func (s *GRPCServer) Logout(ctx context.Context, _ *emptypb.Empty) (*emptypb.Empty, error) {
	authHeaderData, ok := grpcUtils.GetExternalTokenHeaderData(ctx)
	if !ok {
		return nil, status.Errorf(codes.InvalidArgument, "Invalid request")
	}
	logger.Debugf("Logout request received. Incoming token data: %v", authHeaderData)

	userData := models.User{}
	transactionFunc := func(tx *gorm.DB) error {
		logger.Debug("Retrieving user")
		dbResult := s.DB.Model(&userData).Joins("left join user_statuses on users.id = user_statuses.user_id").
			Where("user_statuses.status <> ?", "DEL").
			Where("user_statuses.current = ?", "TRUE").
			Where("LOWER(users.email) = ?", strings.ToLower(authHeaderData.Email)).
			First(&userData)
		logger.Debugf("User result: %v", dbResult)
		if dbResult.Error != nil {
			logger.Errorf("error during getting user status: %v", dbResult.Error)
			if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
				return status.Errorf(codes.NotFound, "User not found for email: \"%v\"", authHeaderData.Email)
			}
			return status.Errorf(codes.Unknown, "unexpected error")
		}
		logger.Debugf("Retrieved user: %v", userData)
		userData.LastLogoutDate = &sql.NullTime{Valid: true, Time: time.Now()}

		logger.Debug("Updating user's last logout time")
		dbResult = tx.Model(&userData).UpdateColumn("last_logout_date", userData.LastLogoutDate)
		if dbResult.Error != nil {
			logger.Errorf("error during user update: %v", dbResult.Error)
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		logger.Debug("User updated successfully with new logout time")
		return nil
	}
	err := s.DB.Transaction(transactionFunc)
	if err != nil {
		return nil, err
	}

	// Set the expired cookie in the gRPC metadata
	expiredCookie := formatExpiredCookie()
	err = grpc.SetHeader(ctx, metadata.Pairs("Set-Cookie", expiredCookie))
	if err != nil {
		logger.Errorf("Failed to set expired cookie in metadata: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	return &emptypb.Empty{}, nil
}

func formatExpiredCookie() string {
	authCookieName := "geti-cookie"
	return authCookieName + "=; Max-Age=0; HttpOnly; SameSite=Strict; Secure; Path=/"
}

func (s *GRPCServer) Delete(_ context.Context, req *pb.UserIdRequest) (*emptypb.Empty, error) {
	logger.Infof("delete user request: organization ID %s, user ID %s", req.OrganizationId, req.UserId)
	parsedUuid, err := uuid.Parse(req.UserId)
	if err != nil {
		logger.Errorf("error during parsing user UUID: %v", err)
		return nil, status.Error(codes.InvalidArgument, "malformed user UUID")
	}

	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize roles manager: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	userRelationships, err := rolesMgr.GetUserAllRelationships(parsedUuid.String())
	if err != nil {
		logger.Errorf("unable to get all user relationships: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	for _, relationship := range userRelationships {
		deleteRelation, err := rolesMgr.CheckRelationshipToDelete(relationship, req.OrganizationId)
		if err != nil {
			logger.Errorf("failed to determine if relationship should be deleted: %v", err)
			return nil, status.Errorf(codes.Unknown, "unexpected error")
		}
		if deleteRelation {
			err := rolesMgr.ChangeUserRelation(relationship.Resource.ObjectType, relationship.Resource.ObjectId, []string{relationship.Relation}, req.UserId, authzed.RelationshipUpdate_OPERATION_DELETE)
			if err != nil {
				logger.Errorf("failed to delete user relationship: %v", err)
				return nil, status.Errorf(codes.Unknown, "unexpected error")
			}
		}
	}

	pat := models.PersonalAccessToken{}
	patDbResult := s.DB.Model(&pat).Where("status = ? AND user_id = ? AND organization_id = ?", "ACT", req.UserId, req.OrganizationId).Update("status", "DEL")
	if patDbResult.Error != nil {
		logger.Errorf("error during personal access token update: %v", patDbResult.Error)
		return nil, status.Errorf(codes.Unauthenticated, "Unexpected error")
	}

	dbResult := s.DB.Delete(&models.User{ID: parsedUuid})
	if dbResult.Error != nil {
		logger.Errorf("error during deleting user: %v", dbResult.Error)
		return nil, status.Error(codes.Unknown, "unexpected error during deleting user")
	}

	if dbResult.RowsAffected == 0 {
		logger.Errorf("No user found to delete for the UUID: %v", parsedUuid)
		return nil, status.Error(codes.NotFound, "No user found to delete")
	}

	logger.Infof("user %s has been deleted from organization %s", req.UserId, req.OrganizationId)
	return &emptypb.Empty{}, nil
}

func (s *GRPCServer) Modify(ctx context.Context, data *pb.UserData) (*pb.UserData, error) {
	logger.Debugf("user modify request: %v", data)
	parsedUserUUID, err := uuid.Parse(data.Id)
	if err != nil {
		logger.Errorf("error during parsing user's UUID: %v", err)
		return nil, status.Error(codes.InvalidArgument, "malformed user's UUID")
	}

	parsedOrganizationUUID, err := uuid.Parse(data.OrganizationId)
	if err != nil {
		logger.Errorf("error during parsing organization's UUID: %v", err)
		return nil, status.Error(codes.InvalidArgument, "malformed organization's UUID")
	}

	if !grpcUtils.IsEmailValid(data.Email) {
		logger.Errorf("invalid user email: %v", data.Email)
		return nil, status.Errorf(codes.InvalidArgument, "Invalid email: \"%v\" ", data.Email)
	}

	user := models.User{}
	newUserStatus := models.UserStatus{}

	transactionFunc := func(tx *gorm.DB) error {
		dbResult := tx.First(&user, "id = ?", parsedUserUUID.String())
		if dbResult.Error != nil {
			logger.Errorf("error during getting user in modify transaction: %v", dbResult.Error)
			if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
				return status.Errorf(codes.NotFound, "user ID: \"%v\" not found", parsedUserUUID.String())
			}
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		user.FirstName = data.FirstName
		user.SecondName = data.SecondName
		user.Email = strings.ToLower(data.Email)
		user.ExternalId = data.ExternalId
		user.Country = data.Country

		nowTime := sql.NullTime{Valid: true, Time: time.Now()}
		if user.TelemetryConsent != data.TelemetryConsent {
			user.TelemetryConsent = data.TelemetryConsent
			user.TelemetryConsentAt = &nowTime
		}

		if user.UserConsent != data.UserConsent {
			user.UserConsent = data.UserConsent
			user.UserConsentAt = &nowTime
		}

		user.ModifiedBy = data.ModifiedBy

		if data.CurrentSuccessfulLogin != nil {
			user.CurrentSuccessfulLogin = common.TimestampToSqlTime(data.CurrentSuccessfulLogin)
		}
		if data.LastSuccessfulLogin != nil && !data.LastSuccessfulLogin.AsTime().IsZero() {
			user.LastSuccessfulLogin = common.TimestampToSqlTime(data.LastSuccessfulLogin)
		}

		authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if ok {
			user.ModifiedBy = authTokenData.UserID
		}

		result := tx.Model(&models.User{ID: user.ID}).Updates(&user)
		if result.Error != nil {
			logger.Errorf("error during user update: %v", result.Error)
			if grpcUtils.ErrorIsPGUniqueViolation(result.Error, "users_email_key") {
				return status.Errorf(codes.AlreadyExists, "user \"%v\" already exists", data.Email)
			}
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		if data.Status != "" {
			oldCurrentUserStatus := models.UserStatus{}
			dbResult = tx.First(&oldCurrentUserStatus, "user_id = ? AND organization_id = ? AND current = ?", user.ID, parsedOrganizationUUID.String(), "TRUE")
			if dbResult.Error != nil {
				logger.Errorf("error during getting user status: %v", dbResult.Error)
				if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
					return status.Errorf(codes.NotFound, "User status not found for user ID: \"%v\" and organization ID: \"%v\"", user.ID, parsedOrganizationUUID.String())
				}
				return status.Errorf(codes.Unknown, "unexpected error")
			}

			err := fsm.UserStatusFSM.Transition(oldCurrentUserStatus.Status, data.Status)
			if err != nil {
				logger.Errorf("error validating user status transition: %v", err)
				return status.Errorf(codes.FailedPrecondition, "incorrect status")
			}

			if data.Status == "DEL" {
				err = common.CheckIfLastRegisteredOrgAdmin(s.DB, parsedOrganizationUUID.String(), user.ID.String())
				if err != nil {
					return err
				}

				pat := models.PersonalAccessToken{}
				patDbResult := s.DB.Model(&pat).Where("status = ? AND user_id = ? AND organization_id = ?", "ACT", user.ID, parsedOrganizationUUID.String()).Update("status", "DEL")
				if patDbResult.Error != nil {
					logger.Errorf("error during personal access token update: %v", patDbResult.Error)
					return status.Errorf(codes.Unauthenticated, "Unexpected error")
				}

				rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
				if err != nil {
					logger.Errorf("unable to initialize roles manager: %v", err)
					return status.Errorf(codes.Unknown, "unexpected error")
				}

				userRelationships, err := rolesMgr.GetUserAllRelationships(user.ID.String())
				if err != nil {
					logger.Errorf("unable to get all user relationships: %v", err)
					return status.Errorf(codes.Unknown, "unexpected error")
				}

				for _, relationship := range userRelationships {
					deleteRelation, err := rolesMgr.CheckRelationshipToDelete(relationship, parsedOrganizationUUID.String())
					if err != nil {
						logger.Errorf("failed to determine if relationship should be deleted: %v", err)
						return status.Errorf(codes.Unknown, "unexpected error")
					}
					if deleteRelation {
						err := rolesMgr.ChangeUserRelation(relationship.Resource.ObjectType, relationship.Resource.ObjectId, []string{relationship.Relation}, user.ID.String(), authzed.RelationshipUpdate_OPERATION_DELETE)
						if err != nil {
							logger.Errorf("failed to delete user relationship: %v", err)
							return status.Errorf(codes.Unknown, "unexpected error")
						}
					}
				}
			}

			oldCurrentUserStatus.Current = false

			result = tx.Save(&oldCurrentUserStatus)
			if result.Error != nil {
				logger.Errorf("error during user status update: %v", result.Error)
				return status.Errorf(codes.Unknown, "unexpected error")
			}

			newUserStatus = models.UserStatus{
				Status:         data.Status,
				OrganizationID: parsedOrganizationUUID,
				UserID:         parsedUserUUID,
				Current:        true,
			}

			result = tx.Create(&newUserStatus)
			if result.Error != nil {
				logger.Errorf("error during user status Create: %v", result.Error)
				return status.Errorf(codes.Unknown, "unexpected error")
			}

		}

		return nil
	}

	err = s.DB.Transaction(transactionFunc)
	if err != nil {
		return nil, err
	}

	return s.addOrganizationIdsToResponse(user)
}

func (s *GRPCServer) AddPhoto(srv pb.User_AddPhotoServer) error {
	req, err := srv.Recv()
	if err != nil {
		logger.Errorf("unexpected error during user AddPhoto: %v", err)
		return status.Error(codes.Unknown, "unexpected error")
	}

	userID := req.GetUserData().GetUserId()

	user, err := GetUserFromDBByID(s.DB, userID)
	if err != nil {
		return err
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

	s3handle, err := storage.NewS3Storage(config.S3UserPhotosBucketName)
	if err != nil {
		logger.Errorf("unexpected error during AddPhoto: %v", err)
		return status.Error(codes.Unknown, "unexpected error")
	}

	newLocation, err := s3handle.PutObject(imageData, user.ID.String())

	if err != nil {
		logger.Errorf("unexpected error during AddPhoto - putObject: %v", err)
		return status.Error(codes.Unknown, "unexpected error")
	}

	dbResult := s.DB.Model(&user).Update("photo_location", newLocation)
	if dbResult.Error != nil {
		logger.Errorf("error during updating organization with logo: %v", dbResult.Error)
		return status.Errorf(codes.Unknown, "unexpected error")
	}

	emptyResp := &emptypb.Empty{}
	err = srv.SendAndClose(emptyResp)
	if err != nil {
		logger.Errorf("unexpected error during AddPhoto: %v", err)
		return status.Error(codes.Unknown, "unexpected error")
	}

	return nil
}

func (s *GRPCServer) DeletePhoto(_ context.Context, req *pb.UserIdRequest) (*emptypb.Empty, error) {
	logger.Debugf("delete photo request for user %s", req.UserId)

	userID := req.GetUserId()
	user, err := GetUserFromDBByID(s.DB, userID)
	if err != nil {
		return nil, err
	}

	if user.PhotoLocation == "" {
		return nil, status.Errorf(codes.NotFound, "user ID: \"%v\" has no logo", userID)
	}

	s3handle, err := storage.NewS3Storage(config.S3UserPhotosBucketName)
	if err != nil {
		logger.Errorf("error during deleting user logo: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	err = s3handle.DeleteObject(userID)
	if err != nil {
		logger.Errorf("error during deleting organization logo: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	dbResult := s.DB.Model(&user).Update("photo_location", nil)
	if dbResult.Error != nil {
		logger.Errorf("error during updating organization with logo: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}
	logger.Debugf("successfully deleted %s user's photo", userID)
	return &emptypb.Empty{}, nil
}

func (s *GRPCServer) GetPhoto(grpcCtx context.Context, req *pb.UserIdRequest) (*pb.PreUrlResponse, error) {
	logger.Debugf("get photo request for user %s", req.UserId)
	userID := req.GetUserId()

	user, err := GetUserFromDBByID(s.DB, userID)
	if err != nil {
		return nil, err
	}

	if user.PhotoLocation == "" {
		return nil, status.Errorf(codes.NotFound, "user ID: \"%v\" has no logo", user.ID.String())
	}

	s3handle, err := storage.NewS3Storage(config.S3UserPhotosBucketName)
	if err != nil {
		logger.Errorf("error during getting presigned url for user logo: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	presignedURL, err := common.GetPresignedUrlWithMaybeReplacedHost(grpcCtx, s3handle, user.ID.String())
	if err != nil {
		logger.Errorf("error during getting presigned url for user logo: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	response := pb.PreUrlResponse{
		PresignedUrl: presignedURL,
	}

	return &response, nil
}

func (s *GRPCServer) GetRoles(_ context.Context, req *pb.UserGetRolesRequest) (*pb.UserRolesResponse, error) {
	logger.Debugf("get roles request for the user %s, organization %s, resource type %s",
		req.UserId, req.OrganizationId, req.ResourceType)

	availableResourceTypes := []string{"organization", "workspace", "project"}
	if !slices.Contains(availableResourceTypes, req.ResourceType) {
		return nil, status.Errorf(codes.InvalidArgument, "Invalid resource type: %v", req.ResourceType)
	}

	err := s.userMustExistInDB(req.GetUserId())
	if err != nil {
		return nil, err
	}

	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize client: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	userRelationships, err := rolesMgr.GetUserRelationships(req.GetUserId(), req.GetResourceType())
	if err != nil {
		logger.Errorf("error during get user roles: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	var userRoles []*pb.UserRole

	for _, relationship := range userRelationships {
		userRoles = append(userRoles, &pb.UserRole{
			Role:         relationship.Relation,
			ResourceType: relationship.Resource.ObjectType,
			ResourceId:   relationship.Resource.ObjectId,
		})
	}

	response := pb.UserRolesResponse{
		Roles: userRoles,
	}
	return &response, nil
}

func ChangeUserRelationsByRoleOperations(userID string, roleOps []*pb.UserRoleOperation) ([]*pb.UserRoleOperation, error) {
	var roleOpsAlreadyApplied []*pb.UserRoleOperation
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize client: %v", err)
		return roleOpsAlreadyApplied, status.Errorf(codes.Unknown, "unexpected error")
	}

	for _, roleOp := range roleOps {
		role := roleOp.GetRole()
		op := roleOp.GetOperation()
		var authzedOp authzed.RelationshipUpdate_Operation
		switch op {
		case "CREATE":
			authzedOp = authzed.RelationshipUpdate_OPERATION_CREATE
		case "DELETE":
			authzedOp = authzed.RelationshipUpdate_OPERATION_DELETE
		case "TOUCH":
			authzedOp = authzed.RelationshipUpdate_OPERATION_TOUCH
		default:
			logger.Errorf("invalid op: %v", op)
			return roleOpsAlreadyApplied, status.Errorf(codes.InvalidArgument, "invalid operation")
		}

		err := rolesMgr.ChangeUserRelation(role.ResourceType, role.ResourceId, []string{role.Role}, userID, authzedOp)
		if err != nil {
			logger.Errorf("error during setting roles: %v", err)
			var invalidRoleError *roles.InvalidRoleError
			ok := errors.As(err, &invalidRoleError)
			if ok {
				return roleOpsAlreadyApplied, status.Errorf(codes.FailedPrecondition, "%s", invalidRoleError.Error())
			}
			var alreadyExistsError *roles.RoleAlreadyExistsError
			ok = errors.As(err, &alreadyExistsError)
			if ok {
				return roleOpsAlreadyApplied, status.Errorf(codes.AlreadyExists, "%s", alreadyExistsError.Error())
			}

			return roleOpsAlreadyApplied, status.Errorf(codes.Unknown, "unexpected error")
		}
		roleOpsAlreadyApplied = append(roleOpsAlreadyApplied, roleOp)
	}
	logger.Infof("user %s roles have been updated: %v", userID, roleOpsAlreadyApplied)
	return roleOpsAlreadyApplied, nil
}

func RollbackRoleOps(alreadyAppliedRoleOps []*pb.UserRoleOperation, userID string) {
	rollbackInitRolesOps := make([]*pb.UserRoleOperation, len(alreadyAppliedRoleOps))
	copy(rollbackInitRolesOps, alreadyAppliedRoleOps)

	for _, roleop := range rollbackInitRolesOps {
		switch roleop.Operation {
		case "CREATE", "TOUCH":
			roleop.Operation = "DELETE"
		case "DELETE":
			roleop.Operation = "CREATE"
		}
	}

	_, err := ChangeUserRelationsByRoleOperations(userID, rollbackInitRolesOps)
	if err != nil {
		logger.Errorf("failed to rollback roles: %v", err)
	}
}

func (s *GRPCServer) SetRoles(_ context.Context, req *pb.UserRolesRequest) (*emptypb.Empty, error) {
	err := s.userMustExistInDB(req.GetUserId())
	if err != nil {
		return nil, err
	}

	roleOps := req.GetRoles()

	roleOpsAlreadyApplied, err := ChangeUserRelationsByRoleOperations(req.GetUserId(), roleOps)
	if err != nil {
		RollbackRoleOps(roleOpsAlreadyApplied, req.GetUserId())
		return nil, err
	}

	return &emptypb.Empty{}, nil
}

// utility function to extend a list of roles with workspace level roles when they are missing
func UpdateRolesList(rolesList []*pb.UserRoleOperation, organizationId string, ctx context.Context, db *gorm.DB) ([]*pb.UserRoleOperation, error) {
	//get the default workspace
	workspaces, count, err := repository.NewWorkspaceRepository(db).FindWorkspaces(ctx, models.FindWorkspaceRequest{OrganizationId: organizationId})

	if err != nil || count == 0 {
		logger.Errorf("error getting default workspace: %v", err)
		return nil, status.Errorf(codes.Unknown, "error while getting default workspace")
	}

	returnedRoles := serviceUtils.UpdateMissingWorkspaceRoles(rolesList, workspaces[0].ID.String())

	return returnedRoles, nil
}

func (s *GRPCServer) SendInvitation(ctx context.Context, req *pb.UserInvitationRequest) (*pb.UserInvitationResponse, error) {
	logger.Debugf("send user invitation request for user %s from organization %s", req.User.Id, req.User.OrganizationId)
	var userInvitationResponse pb.UserInvitationResponse
	var userRoles []*pb.UserRoleOperation

	transaction := func(tx *gorm.DB) error {
		org := models.Organization{}

		authTokenData, authTokenDataPresent := grpcUtils.GetAuthTokenHeaderData(ctx)

		orgRequestedID, err := uuid.Parse(req.User.OrganizationId)
		if err != nil {
			logger.Errorf("error during parsing organization uuid: %v", err)
			return status.Errorf(codes.InvalidArgument, "invalid organization UUID: \"%v\" ", req.User.OrganizationId)
		}

		dbResult := s.DB.First(&org, "id = ?", orgRequestedID.String())
		if dbResult.Error != nil {
			logger.Errorf("error during getting organization: %v", dbResult.Error)
			if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
				return status.Errorf(codes.NotFound, "organization ID: \"%v\" not found", req.User.OrganizationId)
			}
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		userDataInRequest := req.User
		if !grpcUtils.IsEmailValid(userDataInRequest.Email) {
			logger.Errorf("error during invitation sending: invalid user email %v", userDataInRequest.Email)
			return status.Errorf(codes.InvalidArgument, "Invalid email: \"%v\" ", userDataInRequest.Email)
		}

		invitedUser := models.User{
			FirstName:  userDataInRequest.FirstName,
			SecondName: userDataInRequest.SecondName,
			Email:      strings.ToLower(userDataInRequest.Email),
			ExternalId: userDataInRequest.ExternalId,
			Country:    userDataInRequest.Country,
			CreatedBy:  userDataInRequest.CreatedBy,
		}
		if authTokenDataPresent {
			invitedUser.CreatedBy = authTokenData.UserID
		}

		nowTime := sql.NullTime{Valid: true, Time: time.Now()}
		if userDataInRequest.UserConsent != nil && *userDataInRequest.UserConsent != "" {
			invitedUser.UserConsent = userDataInRequest.UserConsent
			invitedUser.UserConsentAt = &nowTime
		}

		if userDataInRequest.TelemetryConsent != nil && *userDataInRequest.TelemetryConsent != "" {
			invitedUser.TelemetryConsent = userDataInRequest.TelemetryConsent
			invitedUser.TelemetryConsentAt = &nowTime
		}

		invitedUserStatus := models.UserStatus{
			Status:         "RGS",
			OrganizationID: org.ID,
			Current:        true,
			CreatedBy:      userDataInRequest.CreatedBy,
		}
		if authTokenDataPresent {
			invitedUserStatus.CreatedBy = authTokenData.UserID
		}

		err = CreateUser(ctx, tx, &invitedUser, &invitedUserStatus)
		if err != nil {
			logger.Errorf("error during creating user: %v", err)
			return err
		}

		//update roles with workspace level roles if required
		userRoles = req.Roles
		if config.FeatureFlagManageUsers {
			userRoles, err = UpdateRolesList(userRoles, orgRequestedID.String(), ctx, tx)
			if err != nil {
				logger.Errorf("error during updating roles: %v", err)
				return err
			}
		}

		roleOpsAlreadyApplied, err := ChangeUserRelationsByRoleOperations(invitedUser.ID.String(), userRoles)
		if err != nil {
			logger.Errorf("error during setting user roles: %v", err)
			RollbackRoleOps(roleOpsAlreadyApplied, invitedUser.ID.String())
			return err
		}

		type InvitationFilling struct {
			InvitationLink   string
			OrganizationName string
		}

		filling := InvitationFilling{
			InvitationLink:   config.InvitationLink,
			OrganizationName: org.Name,
		}

		tmpl, err := template.New("invitation").Parse(config.UserInvitationMailMessage)
		if err != nil {
			logger.Errorf("error during parsing invitation template: %v", err)
			RollbackRoleOps(roleOpsAlreadyApplied, invitedUser.ID.String())
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		var invitationMessage bytes.Buffer
		err = tmpl.Execute(&invitationMessage, filling)
		if err != nil {
			logger.Errorf("error during executing invitation template: %v", err)
			RollbackRoleOps(roleOpsAlreadyApplied, invitedUser.ID.String())
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		message := map[string]string{
			"subject":      config.UserInvitationMailTopic,
			"to":           req.User.Email,
			"from_address": config.InvitationFromAddress,
			"from_name":    config.InvitationFromName,
			"content":      "",
			"html_content": invitationMessage.String(),
		}

		jsonMsg, err := json.Marshal(message)
		if err != nil {
			logger.Errorf("error during marshalling invitation message: %v", err)
			RollbackRoleOps(roleOpsAlreadyApplied, invitedUser.ID.String())
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		err = messaging.SendMessage(config.KafkaTopicPrefix+config.GetiNotificationTopic, jsonMsg)
		if err != nil {
			logger.Errorf("error during pushing invitation message to queue: %v", err)
			RollbackRoleOps(roleOpsAlreadyApplied, invitedUser.ID.String())
			return status.Errorf(codes.Unknown, "unexpected error")
		}

		userInvitationResponse = pb.UserInvitationResponse{
			UserId: invitedUser.ID.String(),
		}

		return nil
	}

	err := s.DB.Transaction(transaction)
	if err != nil {
		return nil, err
	}
	logger.Infof("User invitation from organization %s has been sent to user with ID %s. User roles: %v", req.User.OrganizationId, req.User.Id, userRoles)

	return &userInvitationResponse, nil
}

func (s *GRPCServer) GetUserRoles(ctx context.Context, req *pb.UserPayload) (*pb.RolesResponse, error) {
	if !config.FeatureFlagManageUsersRoles {
		return nil, status.Errorf(codes.Unimplemented, "Invalid endpoint")
	}
	logger.Infof("Fetching roles for user ID: %s in organization ID: %s", req.UserId, req.OrganizationId)

	userID := req.UserId
	if userID == "me" {
		authHeaderData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if !ok {
			logger.Errorf("Unable to fetch user ID from request header")
			return nil, status.Error(codes.Unauthenticated, "user ID missing in headers")
		}
		userID = authHeaderData.UserID
	}

	// Fetch all user relationships within the organization
	userRelationships, err := roleService.GetUserAllRelationshipsByOrganization(req.OrganizationId, userID)
	if err != nil {
		return nil, err
	}

	var retrievedRoles []*pb.RolePayload
	for _, rel := range userRelationships {
		retrievedRoles = append(retrievedRoles, &pb.RolePayload{
			Role:       rel.Relation,
			ResourceId: rel.Resource.ObjectId,
		})
	}

	return &pb.RolesResponse{Roles: retrievedRoles}, nil
}

func (s *GRPCServer) AssignRole(ctx context.Context, req *pb.UserRolePayload) (*emptypb.Empty, error) {
	if !config.FeatureFlagManageUsersRoles {
		return nil, status.Errorf(codes.Unimplemented, "Invalid endpoint")
	}
	logger.Debugf("Assigning role %s to user ID: %s in organization ID: %s", req.Role, req.User.UserId, req.User.OrganizationId)

	if !roleService.IsValidRole(req.Role) {
		logger.Errorf("Invalid role provided: %s", req.Role)
		return nil, status.Errorf(codes.InvalidArgument, "invalid role: %s", req.Role)
	}

	// Extract resource type from role
	parts := strings.Split(req.Role, "_")
	if len(parts) < 2 {
		logger.Errorf("Invalid role format: %s", req.Role)
		return nil, status.Error(codes.InvalidArgument, "invalid role format")
	}
	resourceType := parts[0]

	userRelationships, err := roleService.GetUserAllRelationshipsByOrganization(req.User.OrganizationId, req.User.UserId)
	if err != nil {
		return nil, err
	}

	// Iterate over userRelationships to check for conflicting roles
	err = roleService.DeleteConflictingRoles(resourceType, req.ResourceId, req.User.UserId, userRelationships)
	if err != nil {
		return nil, err
	}

	// Assign the new role
	err = roleService.CreateRole(resourceType, req.ResourceId, req.Role, req.User.UserId)
	if err != nil {
		return nil, err
	}

	// Handle default workspace roles for organization-level roles
	if req.Role == "organization_admin" || req.Role == "organization_contributor" {
		// Retrieve the default workspace
		defaultWorkspace, err := s.WorkspaceService.GetDefaultWorkspace(req.User.OrganizationId)
		if err != nil {
			return nil, err
		}

		// Determine the additional role based on the current role
		additionalRole := "workspace_contributor"
		if req.Role == "organization_admin" {
			additionalRole = "workspace_admin"
		}

		// Iterate over userRelationships to check for conflicting roles for workspace
		err = roleService.DeleteConflictingRoles("workspace", defaultWorkspace.ID.String(), req.User.UserId, userRelationships)
		if err != nil {
			return nil, err
		}

		// Assign the additional role for the default workspace
		err = roleService.CreateRole("workspace", defaultWorkspace.ID.String(), additionalRole, req.User.UserId)
		if err != nil {
			return nil, err
		}
	}

	logger.Debugf("Role %s successfully assigned to user ID: %s", req.Role, req.User.UserId)
	return &emptypb.Empty{}, nil
}

func (s *GRPCServer) RemoveRole(ctx context.Context, req *pb.UserRolePayload) (*emptypb.Empty, error) {
	if !config.FeatureFlagManageUsersRoles {
		return nil, status.Errorf(codes.Unimplemented, "Invalid endpoint")
	}
	logger.Debugf("Removing role %s for user ID: %s in organization ID: %s", req.Role, req.User.UserId, req.User.OrganizationId)

	// Validate role
	validRoles := map[string]struct{}{
		"project_manager":     {},
		"project_contributor": {},
	}
	if _, valid := validRoles[req.Role]; !valid {
		logger.Errorf("Invalid role provided: %s", req.Role)
		return nil, status.Errorf(codes.InvalidArgument, "invalid role: %s", req.Role)
	}

	// Extract resource type from role
	parts := strings.Split(req.Role, "_")
	if len(parts) < 2 {
		logger.Errorf("Invalid role format: %s", req.Role)
		return nil, status.Error(codes.Internal, "unexpected error")
	}
	resourceType := parts[0]

	err := roleService.DeleteRole(resourceType, req.ResourceId, req.Role, req.User.UserId)
	if err != nil {
		return nil, err
	}

	logger.Debugf("Role %s successfully removed for user ID: %s", req.Role, req.User.UserId)
	return &emptypb.Empty{}, nil
}
