// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"fmt"
	"strings"

	sdkentities "geti.com/go_sdk/entities"
	httperrors "geti.com/go_sdk/errors"
)

// InferenceRequest represents a minimal payload required for inference requests.
type InferenceRequest struct {
	OrganizationID string `uri:"organization_id" binding:"required,uuid4"`
	WorkspaceID    string `uri:"workspace_id" binding:"required,uuid4"`
	ProjectID      string `uri:"project_id" binding:"required,len=24,hexadecimal"`
}

// GetActionAndID parses string query parameter into ID and ActionType instances.
func (r InferenceRequest) GetActionAndID(entity string, sType string) (*sdkentities.ID, ActionType, *httperrors.HTTPError) {
	splitResult := strings.Split(entity, ":")
	if len(splitResult) != 2 {
		errMsg := fmt.Sprintf("invalid %s path parameter provided: %s. Expected "+
			"argument in format <%s_id>:<action>", sType, entity, sType)
		return nil, "", httperrors.NewBadRequestError(errMsg)
	}
	id, action := splitResult[0], splitResult[1]
	if !IsActionSupported(action) {
		errMsg := fmt.Sprintf("Action `%s` is not a valid action. Choose one of %s", action, SupportedActions)
		return nil, "", httperrors.NewNotImplementedError(errMsg)
	}
	return &sdkentities.ID{ID: id}, ActionType(action), nil
}
