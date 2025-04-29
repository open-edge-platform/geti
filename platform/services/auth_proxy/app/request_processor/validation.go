// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"fmt"
	asc "geti.com/account_service_grpc"
	v32 "github.com/envoyproxy/go-control-plane/envoy/type/v3"
	"golang.org/x/exp/slices"
	"strings"
)

func (h *RequestHandler) isAuthorizedForRequestedOrganization(organizationId string) bool {
	h.Logger.Debugf("Validating requested OrganizationId (if present) with the one from the token.")
	requestedOrgID := h.ExtractOrgIDFromPath()
	if requestedOrgID != "" {
		ss := strings.Split(organizationId, ",")

		if !slices.Contains(ss, requestedOrgID) {
			h.Logger.Errorf("Requested organization ID (%s) differs from the token organization ID (%s)", requestedOrgID, organizationId)
			return false
		} else {
			h.Logger.Debugf("Requested organization ID (%s) matches the token organization ID (%s)", requestedOrgID, organizationId)
		}
	} else {
		h.Logger.Debugf("Unable to extract OrganizationId from path: %v", h.RequestPath)
	}
	return true
}

func (h *RequestHandler) validateUserOrganization(currentUser *asc.User) error {
	if currentUser.OrganizationId == "" {
		h.setErrorResponse(v32.StatusCode_Forbidden, "User does not belong to any organization")
		return fmt.Errorf("user does not belong to any organization (%+v)", currentUser)
	}

	if !h.isAuthorizedForRequestedOrganization(currentUser.OrganizationId) {
		h.setErrorResponse(v32.StatusCode_Forbidden, "User does not belong to the requested organization")
		return fmt.Errorf("user %s is not authorized to access organization %s", currentUser.UserId, currentUser.OrganizationId)
	}
	return nil
}

func UserHasRequiredRoles(userRoles []string, requiredRoles []string) bool {
	userRolesMap := make(map[string]bool)
	for _, userRole := range userRoles {
		userRolesMap[userRole] = true
	}
	// Check if all required roles are present in the user's roles
	for _, requiredRole := range requiredRoles {
		if _, exists := userRolesMap[requiredRole]; !exists {
			return false
		}
	}
	return true
}
