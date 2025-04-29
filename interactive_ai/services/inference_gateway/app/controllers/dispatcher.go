// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controllers

import (
	"net/http"

	sdkentities "geti.com/go_sdk/entities"
	httperrors "geti.com/go_sdk/errors"
	"github.com/gin-gonic/gin"

	"inference_gateway/app/entities"
	"inference_gateway/app/service"
)

// DispatchRequest dispatches inference request to the proper inference controller method based on the action and handles response
func DispatchRequest(c *gin.Context, ctrl InferenceController, action entities.ActionType, req *entities.InferenceRequest, id *sdkentities.ID) {
	var (
		statusCode int
		rawBytes   []byte
		jsonResp   any
		httpErr    *httperrors.HTTPError
	)

	switch action {
	case entities.Predict:
		statusCode, rawBytes, httpErr = ctrl.Predict(c, req, *id)
	case entities.Explain:
		rawBytes, httpErr = ctrl.Explain(c, req, *id)
	case entities.BatchPredict:
		jsonResp, httpErr = ctrl.BatchPredict(c, req, *id)
	case entities.BatchExplain:
		jsonResp, httpErr = ctrl.BatchExplain(c, req, *id)
	}

	switch {
	case httpErr != nil && httpErr.StatusCode == 404 && httpErr.Error() == service.ErrModelNotFound.Error():
		c.Status(http.StatusNoContent)
	case httpErr != nil:
		_ = c.AbortWithError(httpErr.StatusCode, httpErr)
	case statusCode > 0:
		// to handle statusCode from cacheService
		c.Data(statusCode, "application/json", rawBytes)
	case rawBytes != nil:
		// not cached, but still raw response
		c.Data(http.StatusOK, "application/json", rawBytes)
	default:
		c.JSON(http.StatusOK, jsonResp)
	}
}
