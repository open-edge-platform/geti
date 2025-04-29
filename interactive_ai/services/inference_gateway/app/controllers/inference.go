// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controllers

import (
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	sdkentities "geti.com/go_sdk/entities"
	httperrors "geti.com/go_sdk/errors"
	"github.com/gin-gonic/gin"
	"github.com/go-playground/validator/v10"

	"inference_gateway/app/entities"
	"inference_gateway/app/service"
	"inference_gateway/app/usecase"
)

// MaxBatchPredictions Maximum amount of predictions that are allowed to be processed in one batch request
const MaxBatchPredictions = 20

type InferenceController interface {
	Predict(c *gin.Context, params *entities.InferenceRequest, entityID sdkentities.ID) (int, []byte, *httperrors.HTTPError)
	Explain(c *gin.Context, params *entities.InferenceRequest, entityID sdkentities.ID) ([]byte, *httperrors.HTTPError)
	BatchPredict(c *gin.Context, params *entities.InferenceRequest, entityID sdkentities.ID) (*usecase.BatchPredictionJSON, *httperrors.HTTPError)
	BatchExplain(c *gin.Context, params *entities.InferenceRequest, entityID sdkentities.ID) (*usecase.BatchExplainJSON, *httperrors.HTTPError)
	IsModelReady(c *gin.Context, entityID string) bool
}

// InferenceControllerImpl is a base controller that provides access to underlying usecase/service layer to
// controllers that embeds it
type InferenceControllerImpl struct {
	cacheSrv    service.CacheService
	modelAccess service.ModelAccessService
	predictUC   usecase.Infer[usecase.BatchPredictionJSON]
	explainUC   usecase.Infer[usecase.BatchExplainJSON]

	RequestHandler
}

func NewInferenceControllerImpl(modelAccess service.ModelAccessService, cacheSrv service.CacheService, requestHandler RequestHandler,
	predict usecase.Infer[usecase.BatchPredictionJSON], explain usecase.Infer[usecase.BatchExplainJSON]) *InferenceControllerImpl {
	return &InferenceControllerImpl{
		modelAccess:    modelAccess,
		cacheSrv:       cacheSrv,
		predictUC:      predict,
		explainUC:      explain,
		RequestHandler: requestHandler,
	}
}

var (
	cacheModeToPredictionTypeMap = map[string]entities.CacheMode{
		"always": entities.Always,
		"never":  entities.Never,
		"auto":   entities.Auto,
	}
)

func ValidateModelID(fl validator.FieldLevel) bool {
	field := fl.Field().String()
	if field == "active" {
		return true
	}
	matchHex24 := regexp.MustCompile(`^[a-fA-F0-9]{24}$`).MatchString
	return matchHex24(field)
}

// CacheModeFromString parses a prediction type string. Default fallback value is Never.
func CacheModeFromString(str string) entities.CacheMode {
	cacheMode, ok := cacheModeToPredictionTypeMap[strings.ToLower(str)]
	if !ok {
		cacheMode = entities.Never
	}
	return cacheMode
}

// wrapHTTPError converts non-HTTP errors to corresponding HTTP error type.
// If the input error is already an HTTP error, it is returned unchanged.
// This ensures all errors returned by this function conform to a standard HTTP error interface.
func wrapHTTPError(err error) *httperrors.HTTPError {
	var httpErr *httperrors.HTTPError
	switch {
	case errors.As(err, &httpErr):
		return httpErr
	case errors.Is(err, service.ErrModelNotFound):
		return httperrors.NewNotFoundError(err.Error())
	case errors.Is(err, service.ErrMediaNotSupported):
		return httperrors.NewUnsupportedMediaType(err.Error())
	default:
		return httperrors.NewInternalServerError(err.Error())
	}
}

func (ic *InferenceControllerImpl) Predict(c *gin.Context, params *entities.InferenceRequest, entityID sdkentities.ID) (int, []byte, *httperrors.HTTPError) {
	req, err := ic.NewPredictionRequest(c, params, entityID)
	if err != nil {
		return http.StatusBadRequest, nil, httperrors.NewBadRequestError(err.Error())
	}
	ctx := c.Request.Context()
	// Check cache parameter and retrieve cached result if necessary
	statusCode, cached, ok := ic.cacheSrv.Get(ctx, req)
	if ok {
		return statusCode, cached, nil
	}

	result, err := ic.predictUC.One(ctx, req)
	if err != nil {
		httpErr := wrapHTTPError(err)
		return httpErr.StatusCode, nil, httpErr
	}

	jsonResp, err := req.ToPredictBytes(result)
	if err != nil {
		return http.StatusInternalServerError, nil, httperrors.NewInternalServerError(fmt.Sprintf(
			"failed to construct JSON response from prediction string: %s", err))
	}

	return http.StatusOK, jsonResp, nil
}

func (ic *InferenceControllerImpl) Explain(c *gin.Context, params *entities.InferenceRequest, entityID sdkentities.ID) ([]byte, *httperrors.HTTPError) {
	req, err := ic.NewPredictionRequest(c, params, entityID)
	if err != nil {
		return nil, httperrors.NewBadRequestError(err.Error())
	}
	if req.UseCache == entities.Always {
		return nil, httperrors.NewBadRequestError("Invalid parameter: `use_cache=always` is not supported for the `explain` endpoint.")
	}
	result, err := ic.explainUC.One(c.Request.Context(), req)
	if err != nil {
		return nil, wrapHTTPError(err)
	}

	jsonResp, err := req.ToExplainBytes(result)
	if err != nil {
		return nil, httperrors.NewInternalServerError(fmt.Sprintf("failed to construct JSON response from prediction string: %s", err))
	}

	return jsonResp, nil
}

func (ic *InferenceControllerImpl) batchRequest(c *gin.Context, params *entities.InferenceRequest, entityID sdkentities.ID) (*entities.BatchPredictionRequestData, error) {
	req, err := ic.NewBatchPredictionRequest(c, params, entityID)
	if err != nil {
		return nil, err
	}
	if req.ExceedsMaxPredictions(MaxBatchPredictions) {
		return nil, fmt.Errorf("too many predictions requested: the maximum amount per request is %d", MaxBatchPredictions)
	}
	return req, nil
}

func (ic *InferenceControllerImpl) BatchPredict(c *gin.Context, params *entities.InferenceRequest, entityID sdkentities.ID) (*usecase.BatchPredictionJSON, *httperrors.HTTPError) {
	req, err := ic.batchRequest(c, params, entityID)
	if err != nil {
		return nil, httperrors.NewBadRequestError(err.Error())
	}
	result, err := ic.predictUC.Batch(c.Request.Context(), req)
	if err != nil {
		return nil, wrapHTTPError(err)
	}
	return result, nil
}

func (ic *InferenceControllerImpl) BatchExplain(c *gin.Context, params *entities.InferenceRequest, entityID sdkentities.ID) (*usecase.BatchExplainJSON, *httperrors.HTTPError) {
	req, err := ic.batchRequest(c, params, entityID)
	if err != nil {
		return nil, httperrors.NewBadRequestError(err.Error())
	}
	result, err := ic.explainUC.Batch(c.Request.Context(), req)
	if err != nil {
		return nil, wrapHTTPError(err)
	}
	return result, nil
}

func (ic *InferenceControllerImpl) IsModelReady(c *gin.Context, entityID string) bool {
	return ic.modelAccess.IsModelReady(c.Request.Context(), entityID)
}
