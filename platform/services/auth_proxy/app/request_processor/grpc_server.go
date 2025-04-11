// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"auth_proxy/app/cache"
	"auth_proxy/app/utils"
	"context"
	"fmt"
	configPb "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	extProcPb "github.com/envoyproxy/go-control-plane/envoy/service/ext_proc/v3"
	v32 "github.com/envoyproxy/go-control-plane/envoy/type/v3"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"io"
	"strings"
	"time"
)

var logger = utils.InitializeBasicLogger()

type ExtProcServer struct {
	extProcPb.UnimplementedExternalProcessorServer
	AuthProxyConfig  *AuthProxyConfiguration
	UnauthorizedURLs []string
	JwtTtlGeti       time.Duration
	Cache            *cache.Cache
}

type RequestHandler struct {
	Server              *ExtProcServer
	Logger              *RequestProcessingLogger
	StreamContext       context.Context
	RequestID           string
	RequestPath         string
	RequestHeaders      *extProcPb.HttpHeaders
	Response            *extProcPb.ProcessingResponse
	JwtExternalString   string
	GetiJwtSignedString string
	TokenIssuedAt       time.Time
}

func (s *ExtProcServer) Init() error {
	var err error
	if s.AuthProxyConfig, err = LoadAuthProxyConfiguration(); err != nil {
		return fmt.Errorf("failed to load AuthProxy configuration: %v", err)
	}
	if s.JwtTtlGeti, err = GetJwtTtlGeti(); err != nil {
		return fmt.Errorf("failed to get JWT TTL: %v", err)
	}
	s.UnauthorizedURLs = GetUnauthorizedURLs()
	cacheTTL, err := GetCacheTtl()
	if err != nil {
		return fmt.Errorf("failed to gt cache TTL: %v", err)
	}
	cacheSizeMB, err := GetCacheSizeMB()
	if err != nil {
		return fmt.Errorf("failed to get cache size: %v", err)
	}
	s.Cache = cache.NewCache(cacheTTL, cacheSizeMB)
	return nil
}

func (h *RequestHandler) Init(server *ExtProcServer, ctx context.Context) {
	h.Server = server
	h.Logger = InitializeRequestProcessingLogger(h)
	h.StreamContext = ctx
	h.JwtExternalString = ""
	h.GetiJwtSignedString = ""
	h.RequestID = GenerateRandomString(10)
	h.Response = &extProcPb.ProcessingResponse{
		Response: &extProcPb.ProcessingResponse_RequestHeaders{
			RequestHeaders: &extProcPb.HeadersResponse{},
		},
	}
}

func (s *ExtProcServer) Process(processServer extProcPb.ExternalProcessor_ProcessServer) error {
	ctx := processServer.Context()
	logger.Debug("Context initialized")

	for {
		select {
		case <-ctx.Done():
			logger.Error("Context's done")
			return ctx.Err()
		default:
		}

		h := &RequestHandler{}
		h.Init(s, ctx)

		req, err := processServer.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			h.Logger.Warnf("Couldn't receive stream request: %v", err)
			return status.Errorf(codes.Unknown, "Cannot receive stream request: %v", err)
		}

		switch value := req.Request.(type) {
		case *extProcPb.ProcessingRequest_RequestHeaders:
			h.handleRequestHeaders(value.RequestHeaders)
		default:
			h.Logger.Warnf("Unsupported request type: %v\n", value)
			h.Response = &extProcPb.ProcessingResponse{
				Response: &extProcPb.ProcessingResponse_RequestHeaders{
					RequestHeaders: &extProcPb.HeadersResponse{},
				},
			}
		}

		h.Logger.Debugf("Sending response: %+v\n", h.Response.Response)
		if err := processServer.Send(h.Response); err != nil {
			h.Logger.Errorf("Failed to send response to the ingress gateway: %v", err)
		}
		return nil
	}
}

func (h *RequestHandler) handleRequestHeaders(headers *extProcPb.HttpHeaders) {
	h.RequestHeaders = headers
	pathHeader, headerFound := GetHeaderValue(h.RequestHeaders, HeaderNamePath)
	if !headerFound {
		h.Logger.Errorf("path header not found.")
		h.setErrorResponse(v32.StatusCode_BadRequest, "Bad request")
		return
	}
	h.RequestPath = pathHeader

	if pathHeader == "/api/v1/set_cookie" {
		return
	}

	h.Logger.Debugf("Received request headers: %+v\n", headers)
	h.Logger.Debugf("EndOfStream: %v\n", headers.EndOfStream)

	authorizationHeader, headerFound := GetHeaderValue(h.RequestHeaders, HeaderNameAuthorization)
	if !headerFound {
		h.Logger.Infof("Authorization header not found. Checking for API Key presence...")
		apiKeyHeader, headerFound := GetHeaderValue(h.RequestHeaders, HeaderApiKey)
		if !headerFound {
			h.Logger.Infof("API Key header not found.")
		} else {
			h.Logger.Infof("API Key header found. Performing API key authorization...")
			if err := h.handleByApiKeyHeader(apiKeyHeader); err != nil {
				h.Logger.Errorf("API key authorization failed: %v", err)
				// ImmediateResponse with error is being sent
			}
		}
	} else {
		h.Logger.Infof("Authorization header is present. Performing user authorization...")
		if err := h.handleByAuthHeader(authorizationHeader); err != nil {
			h.Logger.Errorf("User authorization failed: %v", err)
			// ImmediateResponse with error is being sent
		}
	}

	if h.RequestPath == "/api/v1/onboarding/user" {
		h.deleteOnboardingCache()
	}

	if _, returnError := h.Response.Response.(*extProcPb.ProcessingResponse_ImmediateResponse); !returnError {
		if h.GetiJwtSignedString != "" {
			h.Logger.Infof("Request authorization succeeded. Setting %s header with Geti token.", HeaderNameXAuthRequestAccessToken)
			// attach x-auth-request-access-token header to the request
			h.Response = &extProcPb.ProcessingResponse{
				Response: &extProcPb.ProcessingResponse_RequestHeaders{
					RequestHeaders: &extProcPb.HeadersResponse{
						Response: &extProcPb.CommonResponse{
							HeaderMutation: &extProcPb.HeaderMutation{
								SetHeaders: []*configPb.HeaderValueOption{
									{
										Header: &configPb.HeaderValue{
											Key:      HeaderNameXAuthRequestAccessToken,
											RawValue: []byte(h.GetiJwtSignedString),
										},
									},
								},
							},
						},
					},
				},
			}
		}
	}
}

func (h *RequestHandler) handleByAuthHeader(authorizationHeader string) error {
	h.Logger.Debugf("Authorization header value: %v\n", authorizationHeader)
	splitToken := strings.Split(authorizationHeader, "Bearer")
	if len(splitToken) != 2 {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Authorization header is in unexpected format")
		return fmt.Errorf("authorization header is in unexpected format: %s", authorizationHeader)
	}

	h.JwtExternalString = strings.TrimSpace(splitToken[1])
	h.Logger.Debugf("Bearer token: %s", h.JwtExternalString)

	jwtExternal, claimsExternal, err := ParseJwtString(h.JwtExternalString)
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return fmt.Errorf("unknown error occurred while parsing the token '%s': %+v", h.JwtExternalString, err)
	}
	h.Logger.Debugf("Incoming JWT: %+v.", jwtExternal)

	for _, unauthorizedURL := range h.Server.UnauthorizedURLs {
		if unauthorizedURL == h.RequestPath {
			getiJwtSignedString, err := h.CreateGetiAnonymJWT()
			if err != nil {
				h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
				return fmt.Errorf("failed to create internal Geti JWT: %v", err)
			}
			h.GetiJwtSignedString = getiJwtSignedString
			return nil
		}
	}

	// Auth proxy config was not set (on-prem case)
	if h.Server.AuthProxyConfig == nil {
		return h.handleExternalRequest(claimsExternal, h.JwtExternalString)
	}

	issuer, ok := claimsExternal["iss"].(string)
	if !ok {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
		return fmt.Errorf("error while extracting iss from external token: %v", issuer)
	}
	audience, ok := claimsExternal["aud"].(string)
	if !ok {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
		return fmt.Errorf("error while extracting aud from external token: %v", audience)
	}

	// Check if the issuer and audience match either internal (users that have access to admin interface) or external configuration
	if issuer == h.Server.AuthProxyConfig.IssInternal && audience == h.Server.AuthProxyConfig.AudInternal {
		return h.handleIntelAdminRequest(jwtExternal, claimsExternal)
	} else if issuer == h.Server.AuthProxyConfig.IssExternal && audience == h.Server.AuthProxyConfig.AudExternal {
		return h.handleExternalRequest(claimsExternal, h.JwtExternalString)
	}

	h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
	return fmt.Errorf("neither internal not external user configuration found in the token, rejecting the request")
}

func (h *RequestHandler) handleByApiKeyHeader(apiKeyHeader string) error {
	h.Logger.Debugf("API Key header value: %s", apiKeyHeader)
	accessToken := AccessTokenHeader{}
	if err := accessToken.ParseHeaderValue(apiKeyHeader); err != nil {
		h.setErrorResponse(v32.StatusCode_BadRequest, "Bad request")
		return fmt.Errorf("unable to parse the %s header value: %s", HeaderApiKey, apiKeyHeader)
	}
	if !accessToken.IsFormatValid() || !accessToken.IsChecksumValid() {
		h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
		return fmt.Errorf("invalid %s header value: %s", HeaderApiKey, apiKeyHeader)
	}

	patHash, err := accessToken.CalculateHash()
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return fmt.Errorf("unable to calculate hash of '%s' personal access token", apiKeyHeader)
	}

	accessTokenCache, err := h.Server.Cache.GetAccessTokenCache(patHash)
	if err == nil {
		h.Logger.Debugf("Cache HIT for AccessToken related to API key %q", apiKeyHeader)
		if accessTokenCache.ErrorMsg != "" {
			h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
			return fmt.Errorf("cached error for access token: %s", accessTokenCache.ErrorMsg)
		}
		if accessTokenCache.AccessTokenData.ExpiresAt.Before(time.Now().UTC()) {
			h.setErrorResponse(v32.StatusCode_Unauthorized, "Access token is expired")
			return fmt.Errorf("access token (%+v) is expired", accessTokenCache.AccessTokenData)
		}
		if accessTokenCache.AccessTokenData.OrganizationId == "" {
			h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
			return fmt.Errorf("access token does not belong to any organization (%+v)", accessTokenCache.AccessTokenData)
		}
		if !h.isAuthorizedForRequestedOrganization(accessTokenCache.AccessTokenData.OrganizationId) {
			h.setErrorResponse(v32.StatusCode_Unauthorized, "Invalid authorization token")
			return fmt.Errorf("requested organization ID (%s) differs from the token organization ID (%s)", h.RequestPath, accessTokenCache.AccessTokenData.OrganizationId)
		}
		h.GetiJwtSignedString = accessTokenCache.GetiJWT
		return nil
	}

	h.Logger.Debugf("Cache MISS for AccessToken related to API key %q", apiKeyHeader)

	token, err := h.dispatchGetPATRequest(patHash)
	if err != nil {
		newAccessTokenCache := cache.AccessTokenCache{
			GetiJWT:  "",
			ErrorMsg: err.Error(),
		}
		if cacheErr := h.Server.Cache.SetAccessTokenCache(patHash, newAccessTokenCache); cacheErr != nil {
			h.Logger.Errorf("Failed to cache access token error: %v", cacheErr)
		}
		return fmt.Errorf("failed to dispatch get PAT request, or PAT authorization check failed: %v", err)
	}

	getiJwtSignedString, err := h.CreateGetiJWTforPAT(token)
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return fmt.Errorf("failed to create Geti JWT for the API Key '%s': %v", apiKeyHeader, err)
	}
	h.GetiJwtSignedString = getiJwtSignedString

	newAccessTokenCache := cache.AccessTokenCache{
		AccessTokenData: token,
		GetiJWT:         getiJwtSignedString,
		ErrorMsg:        "",
	}
	if err := h.Server.Cache.SetAccessTokenCache(patHash, newAccessTokenCache); err != nil {
		h.Logger.Errorf("Failed to cache access token data: %v", err)
	}

	return nil
}
