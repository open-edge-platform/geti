// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package personal_access_token

import (
	"account_service/app/grpc/common"
	"context"
	"crypto/rand"
	"crypto/sha512"
	"database/sql"
	"encoding/binary"
	"errors"
	"fmt"
	"hash/crc32"
	"math/big"
	"strings"
	"time"

	"account_service/app/config"
	grpcUtils "account_service/app/grpc/utils"
	"account_service/app/models"
	"account_service/app/roles"
	"common/utils"

	"geti.com/account_service_grpc/pb"
	"github.com/google/uuid"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
	"google.golang.org/protobuf/types/known/timestamppb"
	"gorm.io/gorm"
)

type GRPCServer struct {
	pb.UnimplementedPersonalAccessTokenServer
	DB *gorm.DB
}

var logger = utils.InitializeLogger()

func toBase62(bytes []byte) string {
	var i big.Int
	i.SetBytes(bytes[:])
	return i.Text(62)
}

// generatePAT creates personal access token
func generatePAT() (string, error) {
	length := 32
	random := make([]byte, length)
	_, err := rand.Read(random)
	if err != nil {
		logger.Errorf("error: %v", err)
		return "", err
	}

	checksum := crc32.ChecksumIEEE(random)
	checksumBytes := make([]byte, 4)
	binary.LittleEndian.PutUint32(checksumBytes, checksum)

	personalAccessToken := fmt.Sprintf("geti_pat_%043s_%06s", toBase62(random), toBase62(checksumBytes))
	return personalAccessToken, nil
}

func createHashForPAT(token string) (string, error) {
	tokenBytes := []byte(token)
	sha384Hash := sha512.Sum384(tokenBytes)

	hashInt := new(big.Int)
	hashInt.SetBytes(sha384Hash[:])

	// Convert the integer to base62
	sha384HashBase62 := hashInt.Text(62)

	// Left-pad the hash to a length of 65 with zeroes
	paddedHash := leftPadWithZeroes(sha384HashBase62, 65)

	return paddedHash, nil
}

// Function to left-pad a string with zeroes to a given length
func leftPadWithZeroes(str string, length int) string {
	if len(str) >= length {
		return str
	}

	padding := strings.Repeat("0", length-len(str))
	return padding + str
}

func (s *GRPCServer) checkIfUserBelongsToOrganization(userId string, organizationId string) bool {
	// check if user belongs to organization
	var userStatus models.UserStatus
	result := s.DB.
		Where("user_id = ? AND organization_id = ? AND current = ? AND status not in (?, ?)", userId, organizationId, "TRUE", "RGS", "DEL").
		First(&userStatus)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			logger.Debug("User doesnt belong to an organization.")
			return false
		}
		logger.Errorf("Database error: %v", result.Error)
		return false
	}
	return true
}

func (s *GRPCServer) Create(ctx context.Context, request *pb.PersonalAccessTokenCreateRequest) (*pb.PersonalAccessTokenCreateResponse, error) {
	logger.Debug("Creating personal acccess token")

	if request.ExpiresAt.AsTime().Before(time.Now()) {
		logger.Errorf("requested PAT expiration date is invalid")
		return nil, status.Errorf(codes.InvalidArgument, "expiration date from the past")
	}

	var userId uuid.UUID
	var err error

	if config.FeatureFlagAccSvcMod {
		authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if !ok {
			logger.Errorf("Failed to retrieve auth token data: %v", authTokenData)
			return nil, status.Error(codes.Unknown, "unexpected error while creating personal access token")
		}

		userId, err = uuid.Parse(authTokenData.UserID)
		if err != nil {
			logger.Errorf("error during parsing user UUID: %v", err)
			return nil, status.Error(codes.InvalidArgument, "malformed user UUID")
		}
	} else {
		userId, err = uuid.Parse(request.UserId)
		if err != nil {
			logger.Errorf("error during parsing user uuid: %v", err)
			return nil, status.Errorf(codes.InvalidArgument, "invalid user UUID: \"%v\" ", request.UserId)
		}
	}

	organizationId, err := uuid.Parse(request.OrganizationId)
	if err != nil {
		logger.Errorf("error during parsing user uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid organization UUID: \"%v\" ", request.UserId)
	}

	if !s.checkIfUserBelongsToOrganization(userId.String(), organizationId.String()) {
		return nil, status.Error(codes.Unauthenticated, "unauthorized")
	}

	logger.Debug("Generating PAT")
	token, err := generatePAT()
	if err != nil {
		logger.Errorf("Error during personal access token generation: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	logger.Debugf("Creating hash for PAT: %v", token)
	hash, err := createHashForPAT(token)
	if err != nil {
		logger.Errorf("Error during hash generation: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	pat := &models.PersonalAccessToken{
		Hash:           hash,
		Partial:        token[0:20],
		Name:           request.Name,
		Description:    request.Description,
		ExpiresAt:      request.ExpiresAt.AsTime(),
		Status:         "ACT",
		UserID:         userId,
		OrganizationID: organizationId,
		CreatedBy:      request.CreatedBy,
	}
	result := s.DB.Create(&pat)
	if result.Error != nil {
		logger.Errorf("error during user status Create: %v", result.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	dbResult := s.DB.First(&pat) // refresh database entry
	if dbResult.Error != nil {
		logger.Errorf("error during getting user: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}

	logger.Debug("Adding SpiceDB relation")
	rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
	if err != nil {
		logger.Errorf("unable to initialize client: %v", err)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}
	err = rolesMgr.AddServiceAccountToUser(userId.String(), pat.ID.String())
	if err != nil {
		logger.Errorf("Error adding service account to SpiceDB: %v", err)
		return nil, status.Error(codes.Unknown, "unexpected error")
	}

	logger.Infof("Created personal access token for the user %s from organization %s, token's name: %s, expiration date: %s",
		userId, request.OrganizationId, request.Name, request.ExpiresAt.AsTime())

	response := pb.PersonalAccessTokenCreateResponse{
		Id:                  pat.ID.String(),
		Partial:             pat.Partial,
		Name:                pat.Name,
		Description:         pat.Description,
		ExpiresAt:           timestamppb.New(pat.ExpiresAt),
		OrganizationId:      pat.OrganizationID.String(),
		UserId:              pat.UserID.String(),
		CreatedAt:           timestamppb.New(pat.CreatedAt),
		PersonalAccessToken: token,
	}
	return &response, nil
}

func (s *GRPCServer) getActiveToken(hash string) (*models.PersonalAccessToken, error) {
	patToken := &models.PersonalAccessToken{}

	dbResult := s.DB.Where("hash = ? AND status = ? and expires_at > ?", hash, "ACT", time.Now()).First(&patToken)
	if dbResult.Error != nil {
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return nil, status.Errorf(codes.NotFound, "Valid personal access token for hash: \"%v\" not found", hash)
		}
		logger.Errorf("Error during looking for pat hash: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}
	logger.Debugf("Received token data: %v", patToken)
	return patToken, nil
}

func (s *GRPCServer) getTokenById(patId string) (*models.PersonalAccessToken, error) {
	patToken := &models.PersonalAccessToken{}

	dbResult := s.DB.Where("id = ? AND status = ? and expires_at > ?", patId, "ACT", time.Now()).First(&patToken)
	if dbResult.Error != nil {
		if errors.Is(dbResult.Error, gorm.ErrRecordNotFound) {
			return nil, status.Errorf(codes.NotFound, "Valid personal access token for id: \"%v\" not found", patId)
		}
		logger.Errorf("Error during looking for pat id: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unknown, "unexpected error")
	}
	logger.Debugf("Received token data: %v", patToken)
	return patToken, nil
}

func (s *GRPCServer) GetByHash(_ context.Context, request *pb.GetByHashRequest) (*pb.PersonalAccessTokenResponse, error) {
	logger.Debugf("get PAT by hash request, hash value: %s", request.Hash)
	patToken, err := s.getActiveToken(request.Hash)
	if err != nil {
		return nil, err
	}
	response := pb.PersonalAccessTokenResponse{
		Id:             patToken.ID.String(),
		Partial:        patToken.Partial,
		Name:           patToken.Name,
		Description:    patToken.Description,
		ExpiresAt:      timestamppb.New(patToken.ExpiresAt),
		OrganizationId: patToken.OrganizationID.String(),
		UserId:         patToken.UserID.String(),
		CreatedAt:      timestamppb.New(patToken.CreatedAt),
	}
	return &response, nil
}

func (s *GRPCServer) GetOrgFromToken(ctx context.Context, _ *pb.GetOrgFromTokenRequest) (*pb.GetOrganizationByTokenResponse, error) {
	logger.Debug("get organization from PAT request")
	authHeaderData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
	if !ok {
		logger.Debugf("The token cannot be obtained correctly from the header data. Incoming token data: %v", authHeaderData)
		return nil, status.Errorf(codes.InvalidArgument, "Invalid request")
	}

	response := pb.GetOrganizationByTokenResponse{
		OrganizationId: authHeaderData.OrgID,
	}
	logger.Debugf("Returning get organization by token response: %v", &response)
	return &response, nil
}

func (s *GRPCServer) Revoke(ctx context.Context, request *pb.PersonalAccessTokenRevokeRequest) (*emptypb.Empty, error) {
	logger.Debug("PAT revoke request")
	patId, err := uuid.Parse(request.Id)
	if err != nil {
		logger.Error("error during parsing PAT uuid: %v", err)
		return nil, status.Errorf(codes.Unauthenticated, "Unexpected error")
	}

	var userId, orgId uuid.UUID

	if config.FeatureFlagAccSvcMod {
		authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if !ok {
			logger.Errorf("Failed to retrieve auth token data: %v", authTokenData)
			return nil, status.Error(codes.Unknown, "unexpected error while revoking personal access token")
		}

		userId, err = uuid.Parse(authTokenData.UserID)
		if err != nil {
			logger.Errorf("error during parsing user UUID: %v", err)
			return nil, status.Error(codes.InvalidArgument, "malformed user UUID")
		}
		// get organization id from token
		patToken, err := s.getTokenById(patId.String())
		if err != nil {
			logger.Errorf("error during getting token by hash: %v", err)
			return nil, status.Error(codes.InvalidArgument, "missing token")
		}
		// check if user belongs to an organization from token
		orgId = patToken.OrganizationID

		if !s.checkIfUserBelongsToOrganization(userId.String(), orgId.String()) {
			logger.Errorf("User doesnt belong to organization : %v - %v", userId.String(), orgId.String())
			return nil, status.Error(codes.Unauthenticated, "unauthorized")
		}
		// check if a user is an owner of a token
		if userId.String() != patToken.UserID.String() {
			logger.Errorf("User is not an owner of a token: %v - %v", userId.String(), patToken.UserID.String())
			return nil, status.Error(codes.Unauthenticated, "unauthorized")
		}
	} else {
		userId, err = uuid.Parse(request.UserId)
		if err != nil {
			logger.Errorf("error during parsing user uuid: %v", err)
			return nil, status.Errorf(codes.InvalidArgument, "invalid user UUID: \"%v\" ", request.UserId)
		}
		orgId, err = uuid.Parse(request.OrganizationId)
		if err != nil {
			logger.Errorf("error during parsing organization uuid: %v", err)
			return nil, status.Error(codes.Unauthenticated, "Unexpected error")
		}
	}

	transactionFunc := func(tx *gorm.DB) error {
		pat := models.PersonalAccessToken{ID: patId, UserID: userId, OrganizationID: orgId, Status: "ACT"}
		result := tx.First(&pat)
		if result.Error != nil {
			logger.Errorf("error during personal access token revoke operation: %v", result.Error)
			return status.Errorf(codes.Unauthenticated, "Unexpected error")
		}

		pat.Status = "DEL"
		authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if ok {
			pat.ModifiedBy = authTokenData.UserID
		}
		nowTime := time.Now()
		pat.ModifiedAt = &sql.NullTime{Time: nowTime, Valid: true}

		result = tx.Save(&pat)
		if result.Error != nil {
			logger.Errorf("error during personal access token revoke operation: %v", result.Error)
			return status.Errorf(codes.Unauthenticated, "unexpected error")
		}

		rolesMgr, err := roles.NewRolesManager(config.SpiceDBAddress, config.SpiceDBToken)
		if err != nil {
			logger.Errorf("unable to initialize client: %v", err)
			return status.Errorf(codes.Unauthenticated, "unexpected error")
		}
		err = rolesMgr.DeleteServiceAccountFromUser(userId.String(), request.Id)
		if err != nil {
			logger.Errorf("Failure during relation deletion from spicedb: %v", err)
			return status.Errorf(codes.Unauthenticated, "unexpected error")
		}
		return nil
	}

	err = s.DB.Transaction(transactionFunc)
	if err != nil {
		return nil, err
	}
	logger.Infof("Organization %s has revoked %s user's personal access token with id %s",
		request.OrganizationId, request.UserId, request.Id)

	return &emptypb.Empty{}, nil
}

func (s *GRPCServer) Extend(ctx context.Context, request *pb.PersonalAccessTokenExtendRequest) (*pb.PersonalAccessTokenResponse, error) {
	logger.Debug("PAT expiration extend request")

	var userId, orgId, patId uuid.UUID
	var err error

	patId, err = uuid.Parse(request.Id)
	if err != nil {
		logger.Error("error during parsing PAT uuid: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "Malformed token ID")
	}

	orgId, err = uuid.Parse(request.OrganizationId)

	if err != nil {
		logger.Errorf("error during parsing organization uuid: %v", err)
		return nil, status.Error(codes.InvalidArgument, "Malformed organization ID")
	}

	if config.FeatureFlagAccSvcMod {
		authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if !ok {
			logger.Errorf("Failed to retrieve auth token data: %v", authTokenData)
			return nil, status.Error(codes.Unknown, "unexpected error while extending personal access token")
		}

		userId, err = uuid.Parse(authTokenData.UserID)
		if err != nil {
			logger.Errorf("error during parsing user UUID: %v", err)
			return nil, status.Error(codes.InvalidArgument, "malformed user UUID")
		}

		// get organization id from token
		patToken, err := s.getTokenById(patId.String())
		if err != nil {
			logger.Errorf("error during getting token by hash: %v", err)
			return nil, status.Error(codes.InvalidArgument, "missing token")
		}
		// check if user belongs to an organization from token
		tokenOrgId := patToken.OrganizationID

		if !s.checkIfUserBelongsToOrganization(userId.String(), tokenOrgId.String()) {
			logger.Error("User doesnt belong to organization : %v - %v", userId.String(), tokenOrgId.String())
			return nil, status.Error(codes.Unauthenticated, "unauthorized")
		}
		// check if a user is an owner of a token
		if userId.String() != patToken.UserID.String() {
			logger.Error("User is not an owner of a token: %v - %v", userId.String(), patToken.UserID.String())
			return nil, status.Error(codes.Unauthenticated, "unauthorized")
		}

		// check if org id in body is equal to the org id from token
		if orgId.String() != tokenOrgId.String() {
			logger.Error("Organization id from token is different than id from body: %v - %v", orgId.String(), request.OrganizationId)
			return nil, status.Error(codes.Unauthenticated, "unauthorized")
		}
	} else {
		userId, err = uuid.Parse(request.UserId)
		if err != nil {
			logger.Error("error during parsing user uuid: %v", err)
			return nil, status.Errorf(codes.InvalidArgument, "Malformed User ID")
		}
	}

	transactionFunc := func(tx *gorm.DB) error {
		pat := models.PersonalAccessToken{ID: patId, UserID: userId, OrganizationID: orgId, Status: "ACT"}
		result := tx.First(&pat)
		if result.Error != nil {
			logger.Errorf("error during personal access token expiration extend operation: %v", result.Error)
			return status.Errorf(codes.Unauthenticated, "Unexpected error")
		}

		pat.ExpiresAt = request.ExpiresAt.AsTime()
		authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
		if ok {
			pat.ModifiedBy = authTokenData.UserID
		}
		nowTime := time.Now()
		pat.ModifiedAt = &sql.NullTime{Time: nowTime, Valid: true}

		result = tx.Save(&pat)
		if result.Error != nil {
			logger.Errorf("error during personal access token expiration extend operation: %v", result.Error)
			return status.Errorf(codes.Unauthenticated, "unexpected error")
		}
		return nil
	}

	err = s.DB.Transaction(transactionFunc)
	if err != nil {
		return nil, err
	}

	pat := models.PersonalAccessToken{ID: patId, UserID: userId, OrganizationID: orgId, Status: "ACT"}
	dbResult := s.DB.First(&pat)
	if dbResult.Error != nil {
		logger.Errorf("error during getting personal access token: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unauthenticated, "unexpected error")
	}
	logger.Infof("Organization %s has extended expiration for %s user's personal access token with id %s, new expiration date: %v",
		request.OrganizationId, request.UserId, request.Id, request.ExpiresAt.AsTime())

	response := pb.PersonalAccessTokenResponse{
		Id:             pat.ID.String(),
		Partial:        pat.Partial,
		Name:           pat.Name,
		Description:    pat.Description,
		ExpiresAt:      timestamppb.New(pat.ExpiresAt),
		OrganizationId: pat.OrganizationID.String(),
		UserId:         pat.UserID.String(),
		CreatedAt:      timestamppb.New(pat.CreatedAt),
	}

	return &response, nil
}

func (s *GRPCServer) Find(ctx context.Context, request *pb.PersonalAccessTokenFindRequest) (*pb.ListPersonalAccessTokensResponse, error) {
	logger.Debug("PAT find request")
	var pats []models.PersonalAccessToken

	statementSession := s.DB.WithContext(ctx)
	statementSession = statementSession.Model(&pats)

	statementSession = statementSession.Where("status = ? AND user_id = ? AND organization_id = ?", "ACT", request.UserId, request.OrganizationId)

	if request.Name != "" {
		statementSession = statementSession.Where("name = ?", request.Name)
	}
	if request.Description != "" {
		statementSession = statementSession.Where("description = ?", request.Description)
	}
	if request.Partial != "" {
		statementSession = statementSession.Where("partial = ?", request.Partial)
	}
	if request.CreatedAtFrom != nil && request.CreatedAtTo != nil {
		statementSession = statementSession.Where(
			"created_at BETWEEN ? AND ?", request.CreatedAtFrom.AsTime(), request.CreatedAtTo.AsTime(),
		)
	} else if request.CreatedAtFrom != nil {
		statementSession = statementSession.Where("created_at > ?", request.CreatedAtFrom.AsTime())
	} else if request.CreatedAtTo != nil {
		statementSession = statementSession.Where("created_at < ?", request.CreatedAtTo.AsTime())
	}

	if request.ExpiresAtFrom != nil && request.ExpiresAtTo != nil {
		statementSession = statementSession.Where(
			"expires_at BETWEEN ? AND ?", request.ExpiresAtFrom.AsTime(), request.ExpiresAtTo.AsTime(),
		)
	} else if request.ExpiresAtFrom != nil {
		statementSession = statementSession.Where("expires_at > ?", request.ExpiresAtFrom.AsTime())
	} else if request.ExpiresAtTo != nil {
		statementSession = statementSession.Where("expires_at < ?", request.ExpiresAtTo.AsTime())
	}

	if request.SortBy != "" && request.SortDirection != "" {
		orderQuery, err := common.CreateOrderQuery(models.PersonalAccessToken{}, request.SortBy, request.SortDirection)
		if err != nil {
			return nil, err
		}

		statementSession = statementSession.Order(orderQuery).Order("id")
	}

	dbResult := statementSession.Find(&pats)
	if dbResult.Error != nil {
		logger.Errorf("error during personal access token find: %v", dbResult.Error)
		return nil, status.Errorf(codes.Unauthenticated, "Unexpected error")
	}

	var result pb.ListPersonalAccessTokensResponse
	for _, pat := range pats {
		foundPat := pb.PersonalAccessTokenResponse{
			Id:             pat.ID.String(),
			Partial:        pat.Partial,
			Name:           pat.Name,
			Description:    pat.Description,
			ExpiresAt:      timestamppb.New(pat.ExpiresAt),
			OrganizationId: pat.OrganizationID.String(),
			UserId:         pat.UserID.String(),
			CreatedAt:      timestamppb.New(pat.CreatedAt),
		}
		result.PersonalAccessTokens = append(result.PersonalAccessTokens, &foundPat)
	}

	return &result, nil
}
