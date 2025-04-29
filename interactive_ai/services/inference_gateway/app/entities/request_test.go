// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"fmt"
	"testing"

	sdkentities "geti.com/go_sdk/entities"
	"github.com/stretchr/testify/assert"
)

func TestInferenceRequest_GetActionAndID(t *testing.T) {
	tests := []struct {
		name       string
		giveParam  string
		wantError  string
		wantID     *sdkentities.ID
		wantAction ActionType
	}{
		{
			name:      "ErrBadRequest_OneParam",
			giveParam: "invalid",
			wantError: "invalid pipeline path parameter provided: invalid. Expected argument in format <pipeline_id>:<action>",
		},
		{
			name:      "ErrBadRequest_ThreeParams",
			giveParam: "000:001:predict",
			wantError: "invalid pipeline path parameter provided: 000:001:predict. Expected argument in format <pipeline_id>:<action>",
		},
		{
			name:      "ErrBadRequest_UnknownAction",
			giveParam: "000:unknown",
			wantError: fmt.Sprintf("Action `unknown` is not a valid action. Choose one of %v", SupportedActions),
		},
		{
			name:       "OK",
			giveParam:  fmt.Sprintf("%s:%s", "511111111111111111111112", Predict),
			wantID:     &sdkentities.ID{ID: "511111111111111111111112"},
			wantAction: Predict,
		},
	}

	testID := sdkentities.GetFullTestID(t)
	req := &InferenceRequest{
		OrganizationID: testID.OrganizationID.String(),
		WorkspaceID:    testID.WorkspaceID.String(),
		ProjectID:      testID.ProjectID.String(),
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			pipelineID, action, e := req.GetActionAndID(tt.giveParam, "pipeline")
			if tt.wantError != "" {
				assert.ErrorContains(t, e, tt.wantError)
				assert.Empty(t, action)
				assert.Nil(t, pipelineID)
			} else {
				assert.Nil(t, e)
				assert.Equal(t, tt.wantID, pipelineID)
				assert.Equal(t, tt.wantAction, action)
			}
		})
	}
}
