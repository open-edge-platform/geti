// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package controllers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/draw"
	"image/jpeg"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"testing"

	sdkentities "geti.com/go_sdk/entities"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"inference_gateway/app/entities"
	mockservice "inference_gateway/app/mock/service"
	testhelpers "inference_gateway/app/test_helpers"
)

func TestRequestHandler_NewPredictionRequest_File(t *testing.T) {
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	testID := sdkentities.GetFullTestID(t)
	req := &entities.InferenceRequest{
		OrganizationID: testID.OrganizationID.String(),
		WorkspaceID:    testID.WorkspaceID.String(),
		ProjectID:      testID.ProjectID.String(),
	}

	testImage := testhelpers.GetUniformTestImage(500, 250, uint8(111))
	buf := new(bytes.Buffer)
	err := jpeg.Encode(buf, testImage, nil)
	assert.Nil(t, err)

	buffer := new(bytes.Buffer)
	writer := multipart.NewWriter(buffer)
	part, err := writer.CreateFormFile("file", "file.jpg")
	assert.NoError(t, err)
	_, err = io.Copy(part, buf)
	assert.NoError(t, err)
	err = writer.Close()
	assert.NoError(t, err)

	roiString := "1,2,3,4"
	roi := entities.Roi{X: 1, Y: 2, Width: 3, Height: 4}
	cacheMode := entities.Always

	// Set query parameters for the request
	queryStr := fmt.Sprintf("?roi=%s&use_cache=%s", roiString, cacheMode)
	c.Request, _ = http.NewRequest("GET", queryStr, buffer)
	c.Request.Header.Set("Content-Type", writer.FormDataContentType())

	mediaMock := mockservice.NewMockMediaService(t)
	rh := NewRequestHandlerImpl(mediaMock)
	predictionRequestData, err := rh.NewPredictionRequest(c, req, testID.TestID)
	assert.NoError(t, err)

	decodedImage, err := predictionRequestData.DecodeMedia()
	assert.NoError(t, err)
	assert.Equal(t, roi, predictionRequestData.Roi)
	assert.Equal(t, cacheMode, predictionRequestData.UseCache)
	//assert.Equal(t, buffer, predictionRequestData.Media)
	//assert.Equal(t, testMediaInfo, predictionRequestData.MediaInfo)
	assert.Equal(t, testID.WorkspaceID, predictionRequestData.WorkspaceID)
	assert.Equal(t, testID.OrganizationID, predictionRequestData.OrganizationID)
	assert.Equal(t, testID.ProjectID, predictionRequestData.ProjectID)
	assert.Equal(t, testID.TestID, predictionRequestData.ModelID)

	// Convert the decodedImage to RGBA to be able to compare with the original
	b := decodedImage.Bounds()
	m := image.NewRGBA(image.Rect(0, 0, b.Dx(), b.Dy()))
	draw.Draw(m, m.Bounds(), decodedImage, b.Min, draw.Src)
	assert.Equal(t, testImage, m)
}

func TestRequestHandler_NewPredictionRequest_Image(t *testing.T) {
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	fullImageID := sdkentities.GetFullImageID(t)
	req := &entities.InferenceRequest{
		OrganizationID: fullImageID.OrganizationID.String(),
		WorkspaceID:    fullImageID.WorkspaceID.String(),
		ProjectID:      fullImageID.ProjectID.String(),
	}

	testImage := testhelpers.GetUniformTestImage(500, 250, uint8(111))
	buf := new(bytes.Buffer)
	err := jpeg.Encode(buf, testImage, nil)
	assert.Nil(t, err)
	requestInfo := &MediaInfoJSON{
		ImageID:   fullImageID.ImageID.String(),
		DatasetID: fullImageID.DatasetID.String(),
	}

	body, err := json.Marshal(requestInfo)
	assert.NoError(t, err)

	roiString := "1,2,3,4"
	roi := entities.Roi{X: 1, Y: 2, Width: 3, Height: 4}
	cacheMode := entities.Always

	// Set query parameters for the request
	queryStr := fmt.Sprintf("?roi=%s&use_cache=%s", roiString, cacheMode)
	c.Request, _ = http.NewRequest("GET", queryStr, bytes.NewBuffer(body))

	mediaMock := mockservice.NewMockMediaService(t)
	mediaMock.EXPECT().GetImage(c.Request.Context(), fullImageID).Return(buf, nil).Once()
	rh := NewRequestHandlerImpl(mediaMock)
	modelID := fullImageID.ImageID
	predictionRequestData, err := rh.NewPredictionRequest(c, req, modelID)
	assert.NoError(t, err)

	decodedImage, err := predictionRequestData.DecodeMedia()
	assert.NoError(t, err)
	assert.Equal(t, roi, predictionRequestData.Roi)
	assert.Equal(t, cacheMode, predictionRequestData.UseCache)
	assert.Equal(t, buf, predictionRequestData.Media)
	testMediaInfo := entities.MediaInfo{
		ImageID:   fullImageID.ImageID,
		DatasetID: fullImageID.DatasetID,
	}
	assert.Equal(t, testMediaInfo, predictionRequestData.MediaInfo)
	assert.Equal(t, fullImageID.WorkspaceID, predictionRequestData.WorkspaceID)
	assert.Equal(t, fullImageID.OrganizationID, predictionRequestData.OrganizationID)
	assert.Equal(t, fullImageID.ProjectID, predictionRequestData.ProjectID)
	assert.Equal(t, modelID, predictionRequestData.ModelID)

	// Convert the decodedImage to RGBA to be able to compare with the original
	b := decodedImage.Bounds()
	m := image.NewRGBA(image.Rect(0, 0, b.Dx(), b.Dy()))
	draw.Draw(m, m.Bounds(), decodedImage, b.Min, draw.Src)
	assert.Equal(t, testImage, m)
}

func TestRequestHandler_NewPredictionRequest_Video(t *testing.T) {
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	fullVideoID := sdkentities.GetFullVideoID(t)
	req := &entities.InferenceRequest{
		OrganizationID: fullVideoID.OrganizationID.String(),
		WorkspaceID:    fullVideoID.WorkspaceID.String(),
		ProjectID:      fullVideoID.ProjectID.String(),
	}
	testImage := testhelpers.GetUniformTestImage(500, 250, uint8(111))
	buf := new(bytes.Buffer)
	err := jpeg.Encode(buf, testImage, nil)
	assert.Nil(t, err)
	requestInfo := &MediaInfoJSON{
		VideoID:    fullVideoID.VideoID.String(),
		DatasetID:  fullVideoID.DatasetID.String(),
		FrameIndex: "1",
	}

	body, err := json.Marshal(requestInfo)
	assert.NoError(t, err)

	roiString := "1,2,3,4"
	roi := entities.Roi{X: 1, Y: 2, Width: 3, Height: 4}
	cacheMode := entities.Always

	// Set query parameters for the request
	queryStr := fmt.Sprintf("?roi=%s&use_cache=%s", roiString, cacheMode)
	c.Request, _ = http.NewRequest("GET", queryStr, bytes.NewBuffer(body))

	mediaMock := mockservice.NewMockMediaService(t)
	mediaMock.EXPECT().GetFrame(c.Request.Context(), fullVideoID, 1).Return(buf, nil).Once()
	rh := NewRequestHandlerImpl(mediaMock)
	modelID := fullVideoID.VideoID
	predictionRequestData, err := rh.NewPredictionRequest(c, req, modelID)
	assert.NoError(t, err)

	decodedImage, err := predictionRequestData.DecodeMedia()
	assert.NoError(t, err)
	assert.Equal(t, roi, predictionRequestData.Roi)
	assert.Equal(t, cacheMode, predictionRequestData.UseCache)
	assert.Equal(t, buf, predictionRequestData.Media)
	testMediaInfo := entities.MediaInfo{
		VideoID:    fullVideoID.VideoID,
		DatasetID:  fullVideoID.DatasetID,
		FrameIndex: 1,
	}
	assert.Equal(t, testMediaInfo, predictionRequestData.MediaInfo)
	assert.Equal(t, fullVideoID.WorkspaceID, predictionRequestData.WorkspaceID)
	assert.Equal(t, fullVideoID.OrganizationID, predictionRequestData.OrganizationID)
	assert.Equal(t, fullVideoID.ProjectID, predictionRequestData.ProjectID)
	assert.Equal(t, modelID, predictionRequestData.ModelID)

	// Convert the decodedImage to RGBA to be able to compare with the original
	b := decodedImage.Bounds()
	m := image.NewRGBA(image.Rect(0, 0, b.Dx(), b.Dy()))
	draw.Draw(m, m.Bounds(), decodedImage, b.Min, draw.Src)
	assert.Equal(t, testImage, m)
}

func TestRequestHandler_NewBatchPredictionRequest_Video(t *testing.T) {
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	fullVideoID := sdkentities.GetFullVideoID(t)
	req := &entities.InferenceRequest{
		OrganizationID: fullVideoID.OrganizationID.String(),
		WorkspaceID:    fullVideoID.WorkspaceID.String(),
		ProjectID:      fullVideoID.ProjectID.String(),
	}
	testImage := testhelpers.GetUniformTestImage(500, 250, uint8(111))
	buf := new(bytes.Buffer)
	err := jpeg.Encode(buf, testImage, nil)
	assert.Nil(t, err)
	requestInfo := &MediaInfoBatchJSON{
		MediaInfoJSON: &MediaInfoJSON{
			VideoID:    fullVideoID.VideoID.String(),
			DatasetID:  fullVideoID.DatasetID.String(),
			FrameIndex: "1",
		},
		StartFrame: "0",
		EndFrame:   "5",
		FrameSkip:  "1",
	}

	body, err := json.Marshal(requestInfo)
	assert.NoError(t, err)

	roiString := "1,2,3,4"
	roi := entities.Roi{X: 1, Y: 2, Width: 3, Height: 4}
	cacheMode := entities.Always

	// Set query parameters for the request
	queryStr := fmt.Sprintf("?roi=%s&use_cache=%s", roiString, cacheMode)
	c.Request, _ = http.NewRequest("GET", queryStr, bytes.NewBuffer(body))

	mediaMock := mockservice.NewMockMediaService(t)
	rh := NewRequestHandlerImpl(mediaMock)
	modelID := fullVideoID.VideoID
	batchRequest, err := rh.NewBatchPredictionRequest(c, req, modelID)
	assert.NoError(t, err)

	assert.Equal(t, roi, batchRequest.Roi)
	testMediaInfo := &entities.MediaInfo{
		VideoID:    fullVideoID.VideoID,
		DatasetID:  fullVideoID.DatasetID,
		FrameIndex: 1,
	}
	assert.Equal(t, testMediaInfo, batchRequest.MediaInfo)
	assert.Equal(t, fullVideoID.WorkspaceID, batchRequest.WorkspaceID)
	assert.Equal(t, fullVideoID.OrganizationID, batchRequest.OrganizationID)
	assert.Equal(t, fullVideoID.ProjectID, batchRequest.ProjectID)
	assert.Equal(t, modelID, batchRequest.ModelID)
}
