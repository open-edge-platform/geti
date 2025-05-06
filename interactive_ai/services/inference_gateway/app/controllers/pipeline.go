// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controllers

import (
	"net/http"

	sdkentities "geti.com/iai_core/entities"
	httperrors "geti.com/iai_core/errors"
	"github.com/gin-gonic/gin"

	"inference_gateway/app/entities"
)

type PipelineController struct {
	InferenceController
}

func NewPipelineController(inferenceController InferenceController) *PipelineController {
	return &PipelineController{
		InferenceController: inferenceController,
	}
}

type pipelineStatusRequest struct {
	ProjectID  string `uri:"project_id" binding:"required,len=24,hexadecimal"`
	PipelineID string `uri:"pipeline_id" binding:"required,activeOr24Hex"`
}

// pipelineRequest are extracted from URL path
type pipelineRequest struct {
	PipelineIDAndAction string `uri:"pipeline_id" binding:"required"`

	*entities.InferenceRequest
}

func (r pipelineStatusRequest) GetFullID() string {
	return r.ProjectID + "-" + r.PipelineID
}

func (r pipelineRequest) GetActionAndID() (*sdkentities.ID, entities.ActionType, *httperrors.HTTPError) {
	return r.InferenceRequest.GetActionAndID(r.PipelineIDAndAction, "pipeline")
}

// Status returns the status of the inference server for a specific pipeline
func (pc *PipelineController) Status(c *gin.Context) {
	var params pipelineStatusRequest
	if err := c.ShouldBindUri(&params); err != nil {
		_ = c.AbortWithError(http.StatusBadRequest, httperrors.NewBadRequestError(err.Error()))
		return
	}

	ready := pc.IsModelReady(c, params.GetFullID())

	c.JSON(
		http.StatusOK,
		gin.H{
			"pipeline_ready": ready,
		},
	)
}

func (pc *PipelineController) Infer(c *gin.Context) {
	var params pipelineRequest
	if err := c.ShouldBindUri(&params); err != nil {
		_ = c.AbortWithError(http.StatusBadRequest, httperrors.NewBadRequestError(err.Error()))
		return
	}

	pipelineID, action, httpErr := params.GetActionAndID()
	if httpErr != nil {
		_ = c.AbortWithError(httpErr.StatusCode, httpErr)
		return
	}

	DispatchRequest(c, pc.InferenceController, action, params.InferenceRequest, pipelineID)
}
