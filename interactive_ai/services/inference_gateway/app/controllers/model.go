// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package controllers

import (
	"net/http"

	sdkentities "geti.com/go_sdk/entities"
	httperrors "geti.com/go_sdk/errors"
	"github.com/gin-gonic/gin"

	"inference_gateway/app/entities"
)

// ModelController is a base controller that provides access to underlying usecase/service layer to
// controllers that embeds it
type ModelController struct {
	InferenceController
}

func NewModelController(inferenceController InferenceController) *ModelController {
	return &ModelController{
		InferenceController: inferenceController,
	}
}

type modelStatusRequest struct {
	ProjectID string `uri:"project_id" binding:"required,len=24,hexadecimal"`
	ModelID   string `uri:"model_id" binding:"required,activeOr24Hex"`
}

type modelRequest struct {
	ModelIDAndAction string `uri:"model_id" binding:"required"`

	*entities.InferenceRequest
}

func (r modelStatusRequest) GetFullID() string {
	return r.ProjectID + "-" + r.ModelID
}

func (r modelRequest) GetActionAndID() (*sdkentities.ID, entities.ActionType, *httperrors.HTTPError) {
	return r.InferenceRequest.GetActionAndID(r.ModelIDAndAction, "model")
}

// Status returns the status of the inference server for a specific model
func (mc *ModelController) Status(c *gin.Context) {
	var params modelStatusRequest
	if err := c.ShouldBindUri(&params); err != nil {
		_ = c.AbortWithError(http.StatusBadRequest, httperrors.NewBadRequestError(err.Error()))
		return
	}

	ready := mc.IsModelReady(c, params.GetFullID())

	c.JSON(
		http.StatusOK,
		gin.H{
			"model_ready": ready,
		},
	)
}

func (mc *ModelController) Infer(c *gin.Context) {
	var params modelRequest
	if err := c.ShouldBindUri(&params); err != nil {
		_ = c.AbortWithError(http.StatusBadRequest, httperrors.NewBadRequestError(err.Error()))
		return
	}

	modelID, action, httpErr := params.GetActionAndID()
	if httpErr != nil {
		_ = c.AbortWithError(httpErr.StatusCode, httpErr)
		return
	}

	DispatchRequest(c, mc.InferenceController, action, params.InferenceRequest, modelID)
}
