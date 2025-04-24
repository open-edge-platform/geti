// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"context"
	"errors"

	"account_service/app/common/utils"

	"github.com/golang-jwt/jwt/v5"
	"google.golang.org/grpc/metadata"
)

var logger = utils.InitializeLogger()

type AuthTokenData struct {
	UserID string
	OrgID  string
}

type ExternalTokenData struct {
	Email string
}

func keyFunc(*jwt.Token) (interface{}, error) {
	// This function shall return the verification key for the external JWT,
	// if signature verification is needed in the future.
	return []byte("External JWT verification key placeholder"), nil
}

func parseJwtString(tokenString string) (*jwt.Token, jwt.MapClaims, error) {
	claims := jwt.MapClaims{}
	token, err := jwt.ParseWithClaims(
		tokenString,
		claims,
		keyFunc,
	)

	// Perform signature verification here. Currently invalid signature errors are ignored.
	if err != nil && !errors.Is(err, jwt.ErrTokenSignatureInvalid) {
		return &jwt.Token{}, jwt.MapClaims{}, err
	}

	return token, claims, nil
}

func GetHTTPHeaderFromGRPCContext(grpcContext context.Context, headerName string) (headerValue string, ok bool) {
	md, ok := metadata.FromIncomingContext(grpcContext)
	if !ok {
		logger.Warn("cannot get metadata from grpc context")
		return "", false
	}

	headers, ok := md[headerName]
	if !ok || len(headers) < 1 {
		logger.Warnf("%v header missing", headerName)
		return "", false
	}

	return headers[0], true
}

func GetExternalTokenHeaderData(ctx context.Context) (*ExternalTokenData, bool) {
	internalToken, ok := GetHTTPHeaderFromGRPCContext(ctx, "x-auth-request-access-token")
	if !ok {
		logger.Warn("Error during x-auth-request-access-token header parsing")
	}

	_, claims, err := parseJwtString(internalToken)
	if err != nil {
		logger.Warn("failed to parse JWT")
		return nil, false
	}

	externalTokenStr, ok := claims["external_token"].(string)
	if !ok {
		logger.Warn("external token missing in JWT claims")
		return nil, false
	}

	_, claims, err = parseJwtString(externalTokenStr)
	if err != nil {
		logger.Warn("failed to parse JWT")
		return nil, false
	}

	email, ok := claims["email"].(string)
	if !ok {
		logger.Warnf("failed to extract email from claims: %v", claims)
		return nil, false
	}

	tokenData := ExternalTokenData{Email: email}

	return &tokenData, true
}

func GetAuthTokenHeaderData(ctx context.Context) (*AuthTokenData, bool) {
	tokenStr, ok := GetHTTPHeaderFromGRPCContext(ctx, "x-auth-request-access-token")
	if !ok {
		return nil, false
	}

	_, claims, err := parseJwtString(tokenStr)
	if err != nil {
		logger.Warn("failed to parse JWT")
		return nil, false
	}

	userId, ok := claims["preferred_username"].(string)
	if !ok {
		logger.Warn("user ID missing in JWT claims")
		return nil, false
	}

	orgId, ok := claims["organization_id"].(string)
	if !ok {
		logger.Warn("organization ID missing in JWT claims")
		return nil, false
	}

	tokenData := AuthTokenData{
		UserID: userId,
		OrgID:  orgId,
	}

	return &tokenData, true
}
