// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controllers

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strconv"

	"inference_gateway/app/entities"
	"inference_gateway/app/service"

	sdkentities "geti.com/iai_core/entities"
	"geti.com/iai_core/logger"
	"github.com/gin-gonic/gin"
)

type MediaInfoJSON struct {
	DatasetID  string `json:"dataset_id" binding:"required,len=24,hexadecimal"`
	ImageID    string `json:"image_id,omitempty" binding:"omitempty,len=24,hexadecimal"`
	VideoID    string `json:"video_id,omitempty" binding:"omitempty,len=24,hexadecimal"`
	FrameIndex string `json:"frame_index,omitempty" binding:"omitempty,number"`
}

type MediaInfoBatchJSON struct {
	StartFrame string `json:"start_frame" binding:"number"`
	EndFrame   string `json:"end_frame" binding:"number"`
	FrameSkip  string `json:"frame_skip" binding:"number"`

	*MediaInfoJSON
}

type HyperParametersJSON map[string]interface{}

type RequestHandler interface {
	GetMedia(c *gin.Context, r *entities.InferenceRequest) (*bytes.Buffer, *entities.MediaInfo, error)
	NewPredictionRequest(c *gin.Context, r *entities.InferenceRequest, entityID sdkentities.ID) (*entities.PredictionRequestData, error)
	NewBatchPredictionRequest(c *gin.Context, r *entities.InferenceRequest, entityID sdkentities.ID) (*entities.BatchPredictionRequestData, error)
}

type RequestHandlerImpl struct {
	mediaSrv service.MediaService
}

func NewRequestHandlerImpl(mediaSrv service.MediaService) *RequestHandlerImpl {
	return &RequestHandlerImpl{
		mediaSrv: mediaSrv,
	}
}

// NewPredictionRequest gathers all required data (media, roi, cache info) for handling the prediction request
// and validates the users input
func (ic *RequestHandlerImpl) NewPredictionRequest(c *gin.Context, r *entities.InferenceRequest, entityID sdkentities.ID) (*entities.PredictionRequestData, error) {
	roi, err := entities.RoiFromString(c.Query("roi"))
	if err != nil {
		return nil, err
	}

	//todo: consider implementing custom validators
	useCache := CacheModeFromString(c.Query("use_cache"))
	labelOnly := c.Query("label_only")
	var labelOnlyBool bool
	if labelOnly == "" {
		labelOnlyBool = false
	} else {
		labelOnlyBool, err = strconv.ParseBool(labelOnly)
		if err != nil {
			return nil, err
		}
	}

	if entityID.String() != "active" {
		if err = entityID.IsValid(); err != nil {
			return nil, fmt.Errorf("model ID is not valid: %s", err)
		}
	}

	data := &entities.PredictionRequestData{
		OrganizationID: sdkentities.ID{ID: r.OrganizationID},
		WorkspaceID:    sdkentities.ID{ID: r.WorkspaceID},
		ProjectID:      sdkentities.ID{ID: r.ProjectID},
		ModelID:        entityID,
		Roi:            roi,
		UseCache:       useCache,
		LabelOnly:      labelOnlyBool,
	}

	media, mediaInfo, mediaErr := ic.GetMedia(c, r)
	if mediaErr != nil {
		return nil, mediaErr
	}
	data.Media = media
	data.MediaInfo = *mediaInfo
	hyperParamsStr := c.Query("hyper_parameters")
	if hyperParamsStr != "" {
		if hpErr := json.Unmarshal([]byte(hyperParamsStr), &[]HyperParametersJSON{}); hpErr != nil {
			return nil, hpErr
		}
	}
	data.HyperParameters = &hyperParamsStr
	return data, nil
}

// GetMedia gets a media from a gin request. Also validates media related IDs
func (ic *RequestHandlerImpl) GetMedia(c *gin.Context, r *entities.InferenceRequest) (*bytes.Buffer, *entities.MediaInfo, error) {
	ctx := c.Request.Context()
	var (
		buf              *bytes.Buffer
		mediaRequestInfo MediaInfoJSON
		frameIndex       int
	)

	datasetID := sdkentities.ID{}
	imageID := sdkentities.ID{}
	videoID := sdkentities.ID{}

	// First try to fetch from the form data
	header, formErr := c.FormFile("file")
	if formErr != nil {
		// No file data in body, image id (or video id + frame index) must be provided in body
		if err := c.ShouldBindBodyWithJSON(&mediaRequestInfo); err != nil {
			return nil, nil, err
		}

		frameIndex, _ = strconv.Atoi(mediaRequestInfo.FrameIndex)
		datasetID = sdkentities.ID{ID: mediaRequestInfo.DatasetID}
		imageID = sdkentities.ID{ID: mediaRequestInfo.ImageID}
		videoID = sdkentities.ID{ID: mediaRequestInfo.VideoID}
		var err error
		if !imageID.IsEmptyID() {
			fullImageID := sdkentities.NewFullImageID(r.OrganizationID, r.WorkspaceID, r.ProjectID,
				datasetID.String(), imageID.String())
			buf, err = ic.mediaSrv.GetImage(ctx, fullImageID)
		} else if !videoID.IsEmptyID() {
			fullVideoID := sdkentities.NewFullVideoID(r.OrganizationID, r.WorkspaceID, r.ProjectID,
				datasetID.String(), videoID.String())
			buf, err = ic.mediaSrv.GetFrame(ctx, fullVideoID, frameIndex)
		} else {
			return nil, nil, errors.New("no file data, image or video id found in request")
		}
		// Handle media fetching error
		if err != nil {
			return nil, nil, err
		}
	} else {
		logger.TracingLog(ctx).Infof("File uploaded %s with size %d", header.Filename, header.Size)
		file, err := header.Open()
		if err != nil {
			return nil, nil, fmt.Errorf("cannot open file from the request: %w", err)
		}
		defer func() {
			if err := file.Close(); err != nil {
				logger.TracingLog(ctx).Errorf("Cannot close file: %s", err)
			}
		}()
		buf = bytes.NewBuffer(make([]byte, 0, header.Size))
		if _, err := io.Copy(buf, file); err != nil {
			return nil, nil, fmt.Errorf("could not load image from request: %w", err)
		}
	}

	mediaInfo := &entities.MediaInfo{
		ImageID:    imageID,
		VideoID:    videoID,
		FrameIndex: frameIndex,
		DatasetID:  datasetID,
	}
	return buf, mediaInfo, nil
}

// NewBatchPredictionRequest gathers all required data (media, roi, cache info) for handling the prediction request
func (ic *RequestHandlerImpl) NewBatchPredictionRequest(c *gin.Context, r *entities.InferenceRequest, entityID sdkentities.ID) (*entities.BatchPredictionRequestData, error) {
	var (
		mediaInfoJSON MediaInfoBatchJSON
		frameIndex    int
		frameSkip     int
		startFrame    int
		endFrame      int
	)

	if err := c.ShouldBindBodyWithJSON(&mediaInfoJSON); err != nil {
		return nil, err
	}

	frameIndex, _ = strconv.Atoi(mediaInfoJSON.FrameIndex)
	frameSkip, _ = strconv.Atoi(mediaInfoJSON.FrameSkip)
	startFrame, _ = strconv.Atoi(mediaInfoJSON.StartFrame)
	endFrame, _ = strconv.Atoi(mediaInfoJSON.EndFrame)

	// todo: convert json fields to int and reimplement with in-built validation rules
	// https://github.com/go-playground/validator?tab=readme-ov-file#comparisons
	if frameSkip <= 0 {
		return nil, errors.New("frame_skip must be greater than 0")
	}

	if endFrame < 0 {
		return nil, errors.New("end_frame must be greater than or equal to 0")
	}

	if startFrame < 0 {
		return nil, errors.New("start_frame must be greater than or equal to 0")
	}

	if startFrame > endFrame {
		return nil, errors.New("end_frame must be greater than or equal to start_frame")
	}

	mediaInfo := &entities.MediaInfo{
		ImageID:    sdkentities.ID{ID: mediaInfoJSON.ImageID},
		VideoID:    sdkentities.ID{ID: mediaInfoJSON.VideoID},
		FrameIndex: frameIndex,
		DatasetID:  sdkentities.ID{ID: mediaInfoJSON.DatasetID},
	}
	roi, err := entities.RoiFromString(c.Query("roi"))
	if err != nil {
		return nil, err
	}

	if entityID.String() != "active" {
		if err = entityID.IsValid(); err != nil {
			return nil, fmt.Errorf("model ID is not valid: %s", err)
		}
	}

	data := &entities.BatchPredictionRequestData{
		OrganizationID: sdkentities.ID{ID: r.OrganizationID},
		WorkspaceID:    sdkentities.ID{ID: r.WorkspaceID},
		ProjectID:      sdkentities.ID{ID: r.ProjectID},
		ModelID:        entityID,
		Roi:            roi,
		FrameSkip:      frameSkip,
		StartFrame:     startFrame,
		EndFrame:       endFrame,
		MediaInfo:      mediaInfo,
	}

	return data, nil
}
