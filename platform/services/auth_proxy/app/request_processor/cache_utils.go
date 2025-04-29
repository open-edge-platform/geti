// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"auth_proxy/app/cache"
	"fmt"
	asc "geti.com/account_service_grpc"
	v32 "github.com/envoyproxy/go-control-plane/envoy/type/v3"
)

func (h *RequestHandler) cacheUserData(subject string, currentUser *asc.User) error {
	getiJwtSignedString, err := h.CreateGetiUserJWT(currentUser)
	if err != nil {
		h.setErrorResponse(v32.StatusCode_InternalServerError, "Internal server error")
		return fmt.Errorf("failed to create internal Geti JWT: %v", err)
	}
	h.GetiJwtSignedString = getiJwtSignedString
	userDataToCache := cache.UserDataCache{
		User:    currentUser,
		GetiJWT: getiJwtSignedString,
	}
	return h.Server.Cache.SetUserDataCache(subject, userDataToCache)
}

func (h *RequestHandler) deleteOnboardingCache() {
	_, claimsExternal, err := ParseJwtString(h.JwtExternalString)
	if err != nil {
		h.Logger.Errorf("unknown error occurred while parsing the token '%s': %+v", h.JwtExternalString, err)
	}
	subject, err := claimsExternal.GetSubject()
	if err != nil {
		h.Logger.Errorf("unknown error occurred while parsing the subject of JWT: %v", err)
	}
	h.Server.Cache.DeleteCacheEntry(subject)
	h.Logger.Infof("Cache entry for the JWT subject %q has been successfully deleted during the onboarding", subject)
}
