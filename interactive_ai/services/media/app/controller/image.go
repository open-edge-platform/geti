// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controller

import (
	"errors"
	"io"
	"net/http"

	sdkentities "geti.com/iai_core/entities"
	httperrors "geti.com/iai_core/errors"
	"geti.com/iai_core/logger"
	"geti.com/iai_core/storage"
	"github.com/gin-gonic/gin"

	"media/app/usecase"
)

type ImageController struct {
	getThumbUseCase usecase.IGetOrCreateThumbnail
	imageRepo       storage.ImageRepository
}

type imageRequest struct {
	OrganizationID string `uri:"organization_id" binding:"required,uuid4"`
	WorkspaceID    string `uri:"workspace_id"    binding:"required,uuid4"`
	ProjectID      string `uri:"project_id"      binding:"required,len=24,hexadecimal"`
	DatasetID      string `uri:"dataset_id"      binding:"required,len=24,hexadecimal"`
	ImageID        string `uri:"image_id"        binding:"required,len=24,hexadecimal"` // mongodb
}

func NewImageController(
	getThumbUseCase usecase.IGetOrCreateThumbnail,
	imageRepo storage.ImageRepository,
) *ImageController {
	return &ImageController{
		getThumbUseCase: getThumbUseCase,
		imageRepo:       imageRepo,
	}
}

func sendImage(c *gin.Context, object io.ReadCloser, metadata *sdkentities.ObjectMetadata) {
	headers := map[string]string{
		"Cache-Control": "private, max-age=3600",
	}
	defer func(obj io.ReadCloser) {
		err := obj.Close()
		if err != nil {
			logger.TracingLog(c.Request.Context()).Errorf("Cannot close object: %s", err)
		}
	}(object)
	c.DataFromReader(http.StatusOK, metadata.Size, metadata.ContentType, object, headers)
}

// GetImage implements the full image display handler.
func (ctrl *ImageController) GetImage(c *gin.Context) {
	var params imageRequest

	if err := c.ShouldBindUri(&params); err != nil {
		_ = c.AbortWithError(http.StatusBadRequest, httperrors.NewBadRequestError(err.Error()))
		return
	}

	fullImageID := sdkentities.NewFullImageID(
		params.OrganizationID,
		params.WorkspaceID,
		params.ProjectID,
		params.DatasetID,
		params.ImageID,
	)
	ctx := c.Request.Context()

	logger.TracingLog(ctx).Infof("GetImage called for imageID %s", fullImageID.ImageID)

	loadedImage, metadata, err := ctrl.imageRepo.LoadImageByID(ctx, fullImageID)
	if err != nil {
		_ = c.AbortWithError(http.StatusNotFound, httperrors.NewNotFoundError(err.Error()))
		return
	}
	sendImage(c, loadedImage, metadata)
}

// GetThumbnail retrieves a thumbnail image from the storage. If the thumbnail doesn't exist, it generates a new one, stores it,
// and then serves the newly created thumbnail.
func (ctrl *ImageController) GetThumbnail(c *gin.Context) {
	var params imageRequest

	if err := c.ShouldBindUri(&params); err != nil {
		_ = c.Error(httperrors.NewBadRequestError(err.Error()))
		return
	}

	fullImageID := sdkentities.NewFullImageID(
		params.OrganizationID,
		params.WorkspaceID,
		params.ProjectID,
		params.DatasetID,
		params.ImageID,
	)
	ctx := c.Request.Context()

	logger.TracingLog(ctx).Infof("GetThumbnail called for imageID %s", fullImageID.ImageID)

	thumbnail, metadata, err := ctrl.getThumbUseCase.Execute(ctx, fullImageID)
	if err != nil {
		{
			var notFoundErr *usecase.NotFoundError
			switch {
			case errors.As(err, &notFoundErr):
				_ = c.AbortWithError(http.StatusNotFound, httperrors.NewNotFoundError(err.Error()))
			default:
				_ = c.AbortWithError(http.StatusInternalServerError, httperrors.NewInternalServerError(err.Error()))
			}
		}
		return
	}
	sendImage(c, thumbnail, metadata)
}
