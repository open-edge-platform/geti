// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"fmt"
	asc "geti.com/account_service_grpc"
	extProcPb "github.com/envoyproxy/go-control-plane/envoy/service/ext_proc/v3"
	v32 "github.com/envoyproxy/go-control-plane/envoy/type/v3"
	"github.com/golang-jwt/jwt/v5"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"net/url"
	"time"
)

func (h *RequestHandler) handleExternalRequest(claimsExternal jwt.MapClaims, jwtExternalString string) error {
	subject, err := claimsExternal.GetSubject()
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return fmt.Errorf("unknown error occurred while parsing the subject of JWT: %v", err)
	}
	h.Logger.Debugf("JWT Subject: %q.", subject)

	tokenIssuedAt, err := claimsExternal.GetIssuedAt()
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return fmt.Errorf("error getting token issue time: %v", err)
	}
	h.TokenIssuedAt = tokenIssuedAt.Time

	currentUser, cacheHit, err := h.getUserDataFromCacheOrService(subject, jwtExternalString, claimsExternal)
	if err != nil {
		return err
	}

	if err := h.validateUserOrganization(currentUser); err != nil {
		return err
	}

	if !cacheHit {
		if err := h.cacheUserData(subject, currentUser); err != nil {
			h.Logger.Errorf("Failed to cache user data: %v", err)
		}
	}

	if err := h.updateLastSuccessfulLoginTime(claimsExternal, currentUser); err != nil {
		h.Logger.Warnf("Failed to update user login time: %v", err)
	}

	return nil
}

func (h *RequestHandler) getUserDataFromCacheOrService(subject, jwtExternalString string, claimsExternal jwt.MapClaims) (*asc.User, bool, error) {
	userDataCache, err := h.Server.Cache.GetUserDataCache(subject)
	if err == nil {
		h.Logger.Debugf("Cache HIT for UserData related to JWT %q", jwtExternalString)
		if authTime, err := GetAuthenticationTime(claimsExternal); err == nil && authTime.After(userDataCache.User.CurrentLoginTime) {
			user, err := h.dispatchGetUserRequest(subject)
			return user, false, err
		}
		h.GetiJwtSignedString = userDataCache.GetiJWT
		h.Logger.Debugf("Set GetiJwtSignedString from cache: %q", h.GetiJwtSignedString)
		return userDataCache.User, true, nil
	}

	h.Logger.Debugf("Cache MISS for UserData related to JWT %q", jwtExternalString)
	currentUser, err := h.dispatchGetUserRequest(subject)
	if err != nil {
		return nil, false, fmt.Errorf("failed to get user information (external ID %s): %v", subject, err)
	}
	return currentUser, false, nil
}

func (h *RequestHandler) handleIntelAdminRequest(jwtExternal *jwt.Token, claimsExternal jwt.MapClaims) error {
	getiJwtSignedString, err := h.CreateIntelAdminJWT(jwtExternal, claimsExternal)
	if err != nil {
		return fmt.Errorf("failed to create internal Geti JWT: %v", err)
	}
	h.GetiJwtSignedString = getiJwtSignedString
	return nil
}

func (h *RequestHandler) dispatchGetUserRequest(externalId string) (*asc.User, error) {
	urlEncodedExternalID := url.QueryEscape(externalId)
	h.Logger.Debugf("Making a GET user request to the account service")
	accSvcClient, err := asc.InitializeUsersClient()
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return nil, fmt.Errorf("failed to initialize account service gRPC connection %v", err)
	}
	user, err := accSvcClient.GetUserByExternalId(h.StreamContext, urlEncodedExternalID)
	if !accSvcClient.CloseConnection() {
		h.Logger.Errorf("failed to close gRPC connection to the account service")
	}
	if err != nil {
		st, ok := status.FromError(err)
		if ok {
			if st.Code() == codes.NotFound {
				h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
				return nil, fmt.Errorf("user with external ID \"%v\" not found", externalId)
			}
		}
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return nil, fmt.Errorf("failed to get user information, external ID \"%v\", error: %v", externalId, err)
	}
	h.Logger.Debugf("Fetched active user from the account service: %v", user)

	//  perform token issue time check
	h.Logger.Debugf("Checking if token issue date (%v) is after %v", h.TokenIssuedAt, user.LastLogoutDate)
	if user.LastLogoutDate.After(h.TokenIssuedAt) {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
		return nil, fmt.Errorf("user logged out after token was issued. Token issue time: %v, last logout time: %v", h.TokenIssuedAt, user.LastLogoutDate)
	}
	return user, nil
}

func (h *RequestHandler) updateLastSuccessfulLoginTime(claimsExternal jwt.MapClaims, userData *asc.User) error {
	authTime, err := GetAuthenticationTime(claimsExternal)
	if err != nil {
		return fmt.Errorf("error getting authentication time: %v", err)
	}
	h.Logger.Debugf("Authentication time from CIDaaS: %+v", authTime)

	if authTime.After(userData.CurrentLoginTime) {
		userData.PreviousLoginTime = userData.CurrentLoginTime
		userData.CurrentLoginTime = authTime
		h.Logger.Debugf("Making a PUT user request to the account service")
		accSvcClient, err := asc.InitializeUsersClient()
		if err != nil {
			return fmt.Errorf("failed to initialize account service gRPC connection %v", err)
		}

		err = accSvcClient.UpdateUserData(h.StreamContext, userData)
		if !accSvcClient.CloseConnection() {
			h.Logger.Errorf("failed to close gRPC connection to the account service")
			return nil
		}
		if err != nil {
			return fmt.Errorf("failed to update user (ext id %s) login time: %v", userData.ExternalId, err)
		}
		h.Logger.Debugf("Updated login time for the user with ext id: %v", userData.ExternalId)
	}
	return nil
}

func (h *RequestHandler) dispatchGetPATRequest(pathHash string) (*asc.AccessTokenData, error) {
	h.Logger.Debugf("Making a GET personal access token reguest to the account service")
	accSvcClient, err := asc.InitializePATclient()
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return nil, fmt.Errorf("failed to initialize account service gRPC connection %v", err)
	}
	token, err := accSvcClient.GetPATbyHash(h.StreamContext, pathHash)
	if !accSvcClient.CloseConnection() {
		h.Logger.Errorf("failed to close gRPC connection to the account service")
	}
	if err != nil {
		st, ok := status.FromError(err)
		if ok {
			if st.Code() == codes.NotFound {
				h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
				return nil, fmt.Errorf("personal access token with hash '%s' not found", pathHash)
			}
		}
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return nil, fmt.Errorf("failed to get personal access token with hash '%s', error: %v", pathHash, err)
	}
	h.Logger.Debugf("Fetched PAT from the account service: %v", token)

	if token.ExpiresAt.Before(time.Now().UTC()) {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Access token is expired")
		return nil, fmt.Errorf("access token (%+v) is expired", token)
	}
	if token.OrganizationId == "" {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
		return nil, fmt.Errorf("access token does not belong to any organization (%+v)", token)
	}
	if !h.isAuthorizedForRequestedOrganization(token.OrganizationId) {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
		return nil, fmt.Errorf("requested organization ID (%s) differs from the token organization ID (%s)", h.RequestPath, token.OrganizationId)
	}
	return token, nil
}

func (h *RequestHandler) setErrorResponse(statusCode v32.StatusCode, message string) {
	h.Logger.Infof("Setting error response, code %v, message: %v", statusCode, message)
	h.Response = &extProcPb.ProcessingResponse{
		Response: &extProcPb.ProcessingResponse_ImmediateResponse{
			ImmediateResponse: &extProcPb.ImmediateResponse{
				Status: &v32.HttpStatus{Code: statusCode},
				Body:   []byte(message),
			},
		},
	}
}
