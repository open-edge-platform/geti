// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"crypto/rsa"
	"fmt"
	asc "geti.com/account_service_grpc"
	v32 "github.com/envoyproxy/go-control-plane/envoy/type/v3"
	"github.com/golang-jwt/jwt/v5"
	"strings"
	"time"
)

const issuerGeti = "Intel Geti"

var signingMethodGeti = jwt.SigningMethodRS512

type UserClaims struct {
	Roles             []string `json:"roles"`
	TenantId          string   `json:"tid"`
	PreferredUsername string   `json:"preferred_username"`
	OrganizationId    string   `json:"organization_id"`
	ExternalToken     string   `json:"external_token"`
	IsInternal        string   `json:"is_internal"`
	Source            string   `json:"source"`
	jwt.RegisteredClaims
}

type PatClaims struct {
	OwnerId string `json:"owner_id"`
	UserClaims
}

func NewGetiJwtSignedString(
	externalToken *jwt.Token,
	userId string,
	orgId string,
	signingKey *rsa.PrivateKey,
	verificationKey []byte,
	ttl time.Duration,
	source string,
) (string, error) {
	externalClaims := externalToken.Claims.(jwt.MapClaims)

	audience, err := externalClaims.GetAudience()
	if err != nil {
		return "", err
	}

	tenantId, ok := externalClaims["tid"]
	if !ok {
		tenantId = ""
	}

	var roles []string
	rawRoles, ok := externalClaims["roles"].([]string)
	if ok {
		roles = append(roles, rawRoles...)
	}

	issuedAt := jwt.NewNumericDate(time.Now())
	notBefore := issuedAt
	expiresAt := jwt.NewNumericDate(issuedAt.Add(ttl))

	keyId := GetKeyId(verificationKey)

	claimsNew := &UserClaims{
		Roles:         roles,
		TenantId:      tenantId.(string),
		ExternalToken: externalToken.Raw,
		Source:        source,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    issuerGeti,
			Audience:  audience,
			ExpiresAt: expiresAt,
			NotBefore: notBefore,
			IssuedAt:  issuedAt,
		},
	}
	if len(orgId) != 0 {
		claimsNew.OrganizationId = orgId
	}
	if len(userId) != 0 {
		claimsNew.PreferredUsername = userId
		claimsNew.Subject = userId
	}

	isInternal, ok := externalClaims["isInternal"]
	if ok {
		isInternalStr, ok := isInternal.(string)
		if ok {
			claimsNew.IsInternal = isInternalStr
		}
	}

	getiJwt := jwt.NewWithClaims(signingMethodGeti, claimsNew)
	getiJwt.Header["kid"] = keyId

	signedString, err := getiJwt.SignedString(signingKey)
	if err != nil {
		return "", err
	}

	return signedString, nil
}

func NewGetiJwtSignedStringFromPAT(
	pat *asc.AccessTokenData,
	signingKey *rsa.PrivateKey,
	verificationKey []byte,
	ttl time.Duration,
) (string, error) {

	issuedAt := jwt.NewNumericDate(time.Now())
	notBefore := issuedAt
	expiresAt := jwt.NewNumericDate(issuedAt.Add(ttl))

	keyId := GetKeyId(verificationKey)

	claimsNew := &PatClaims{
		OwnerId: pat.UserId,
		UserClaims: UserClaims{
			PreferredUsername: pat.Id,
			OrganizationId:    pat.OrganizationId,
			Source:            "pat",
			RegisteredClaims: jwt.RegisteredClaims{
				Subject:   pat.Id,
				Issuer:    issuerGeti,
				ExpiresAt: expiresAt,
				NotBefore: notBefore,
				IssuedAt:  issuedAt,
			},
		},
	}

	getiJwt := jwt.NewWithClaims(signingMethodGeti, claimsNew)
	getiJwt.Header["kid"] = keyId

	signedString, err := getiJwt.SignedString(signingKey)
	if err != nil {
		return "", err
	}

	return signedString, nil
}

func (h *RequestHandler) CreateGetiUserJWT(user *asc.User) (string, error) {
	rsaPrivateKey, publicKey, err := GetKeys()
	if err != nil {
		return "", err
	}

	jwtExternal, _, err := ParseJwtString(h.JwtExternalString)
	if err != nil {
		return "", fmt.Errorf("unknown error occurred while parsing the token '%s': %+v", h.JwtExternalString, err)
	}

	selectedOrgId := ""
	orgIds := strings.Split(user.OrganizationId, ",")
	h.Logger.Debugf("Org ids after split: %v", orgIds)

	for _, orgId := range orgIds {
		h.Logger.Debugf("Checking if %v contains org id %v", h.RequestPath, orgId)
		if strings.Contains(h.RequestPath, orgId) {
			h.Logger.Debugf("Org id found in the path header")
			selectedOrgId = orgId
		}
	}
	if selectedOrgId == "" {
		h.Logger.Debugf("Selected organization id is not set")
	}

	getiJwtSignedString, err := NewGetiJwtSignedString(
		jwtExternal,
		user.UserId,
		selectedOrgId,
		rsaPrivateKey,
		publicKey,
		h.Server.JwtTtlGeti,
		"browser",
	)
	if err != nil {
		return "", fmt.Errorf("failed to create Geti JWT for user %v: %+v", user.UserId, err)
	}
	h.Logger.Debugf("New JWT signed string: %s", getiJwtSignedString)
	return getiJwtSignedString, nil
}

func (h *RequestHandler) CreateGetiJWTforPAT(token *asc.AccessTokenData) (string, error) {
	rsaPrivateKey, publicKey, err := GetKeys()
	if err != nil {
		return "", err
	}

	getiJwtSignedString, err := NewGetiJwtSignedStringFromPAT(token, rsaPrivateKey, publicKey, h.Server.JwtTtlGeti)
	if err != nil {
		return "", fmt.Errorf("failed to create anonymous Geti JWT: %+v", err)
	}
	h.Logger.Debugf("New JWT signed string: %s", getiJwtSignedString)
	return getiJwtSignedString, nil
}

func (h *RequestHandler) CreateGetiAnonymJWT() (string, error) {
	rsaPrivateKey, publicKey, err := GetKeys()
	if err != nil {
		return "", err
	}

	jwtExternal, _, err := ParseJwtString(h.JwtExternalString)
	if err != nil {
		return "", fmt.Errorf("unknown error occurred while parsing the token '%s': %+v", h.JwtExternalString, err)
	}

	getiJwtSignedString, err := NewGetiJwtSignedString(
		jwtExternal,
		"",
		"",
		rsaPrivateKey,
		publicKey,
		h.Server.JwtTtlGeti,
		"browser",
	)
	if err != nil {
		return "", fmt.Errorf("failed to create anonymous Geti JWT: %+v", err)
	}
	h.Logger.Debugf("New JWT signed string: %s", getiJwtSignedString)
	return getiJwtSignedString, nil
}

func (h *RequestHandler) CreateIntelAdminJWT(jwtExternal *jwt.Token, claimsExternal jwt.MapClaims) (string, error) {
	rsaPrivateKey, publicKey, err := GetKeys()
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return "", err
	}

	getiJwtSignedString, err := NewGetiJwtSignedString(
		jwtExternal,
		"",
		"",
		rsaPrivateKey,
		publicKey,
		h.Server.JwtTtlGeti,
		"browser",
	)
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return "", fmt.Errorf("failed to create Geti JWT for Intel admin: %+v", err)
	}
	h.Logger.Debugf("New JWT signed string for Intel admin: %s", getiJwtSignedString)

	rolesInterface, ok := claimsExternal["roles"]
	if !ok {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
		return "", fmt.Errorf("roles claim not found in external claims")
	}

	rolesSlice, ok := rolesInterface.([]interface{})
	if !ok {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
		return "", fmt.Errorf("roles claim is not a valid array of interfaces")
	}

	userRoles := make([]string, len(rolesSlice))
	for i, roleInterface := range rolesSlice {
		role, ok := roleInterface.(string)
		if !ok {
			h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
			return "", fmt.Errorf("role is not a valid string in roles array")
		}
		userRoles[i] = role
	}

	if !UserHasRequiredRoles(userRoles, h.Server.AuthProxyConfig.RequiredRoles) {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
		return "", fmt.Errorf("user doesn't have all the required roles")
	}

	return getiJwtSignedString, nil
}
