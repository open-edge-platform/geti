// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"strconv"
	"strings"
	"time"

	sdkentities "geti.com/go_sdk/entities"
)

type CacheMode string

const (
	Always CacheMode = "always"
	Never  CacheMode = "never"
	Auto   CacheMode = "auto"
)

type MediaInfo struct {
	ImageID    sdkentities.ID
	VideoID    sdkentities.ID
	FrameIndex int
	KeyIndex   int
	DatasetID  sdkentities.ID
}

type ImageIdentifier struct {
	ImageID string `json:"image_id"`
	Type    string `json:"type"`
}

type VideoFrameIdentifier struct {
	VideoID    string `json:"video_id"`
	FrameIndex int    `json:"frame_index"`
	KeyIndex   int    `json:"key_index"`
	Type       string `json:"type"`
}

type PredictionJSON struct {
	Predictions json.RawMessage `json:"predictions"`
}

type ExplainJSON struct {
	Maps json.RawMessage `json:"maps"`
}

type ExplainOutput struct {
	ExplainJSON
	Created string `json:"created"`
}

// PredictionOutput can be used in ephemeral cases where there is no media identifier
type PredictionOutput struct {
	PredictionJSON
	Created string `json:"created"`
}

type VideoFramePredictionOutput struct {
	PredictionOutput
	MediaIdentifier VideoFrameIdentifier `json:"media_identifier"`
}

type ImagePredictionOutput struct {
	PredictionOutput
	MediaIdentifier ImageIdentifier `json:"media_identifier"`
}
type VideoFrameExplainOutput struct {
	ExplainOutput
	MediaIdentifier VideoFrameIdentifier `json:"media_identifier"`
}

type ImageExplainOutput struct {
	ExplainOutput
	MediaIdentifier ImageIdentifier `json:"media_identifier"`
}

// GetCurrentTimeString returns current UTC time
var GetCurrentTimeString = func() string {
	currTime := time.Now().UTC().String()
	return strings.Trim(currTime, " UTC")
}

type PredictionRequestData struct {
	OrganizationID  sdkentities.ID
	WorkspaceID     sdkentities.ID
	ProjectID       sdkentities.ID
	ModelID         sdkentities.ID
	Media           *bytes.Buffer
	Roi             Roi
	UseCache        CacheMode
	LabelOnly       bool
	MediaInfo       MediaInfo
	HyperParameters *string
}

// DecodeMedia reads the image from the buffer and returns it
func (pd PredictionRequestData) DecodeMedia() (image.Image, error) {
	decodedImage, _, err := image.Decode(pd.Media)
	if err != nil {
		return nil, fmt.Errorf("failed to decode image: %s", err)
	}
	return decodedImage, nil
}

func (pd PredictionRequestData) GetURL() string {
	var predictionURL = "/api/v1/organizations/" + pd.OrganizationID.String() +
		"/workspaces/" + pd.WorkspaceID.String() + "/projects/" +
		pd.ProjectID.String() + "/datasets/" + pd.MediaInfo.DatasetID.String()

	// Determine if a request needs to be made to the image or video frame endpoint
	if !pd.MediaInfo.ImageID.IsEmptyID() {
		predictionURL += "/media/images/" + pd.MediaInfo.ImageID.String() +
			"/predictions/latest?inf_gateway=true"
	} else {
		predictionURL += "/media/videos/" + pd.MediaInfo.VideoID.String() +
			"/frames/" + strconv.Itoa(pd.MediaInfo.FrameIndex) + "/predictions/latest?inf_gateway=true"
	}
	if pd.ModelID.String() != "active" {
		predictionURL += "&task_id=" + pd.ModelID.String()
	}
	return predictionURL
}

func (pd PredictionRequestData) ToPredictBytes(predictionJSONString string) ([]byte, error) {
	var (
		predictionBytes = []byte(predictionJSONString)
		predictionJSON  PredictionJSON
		err             error
	)

	if err = json.Unmarshal(predictionBytes, &predictionJSON); err != nil {
		return nil, err
	}
	predictionOutput := PredictionOutput{predictionJSON, GetCurrentTimeString()}

	var jsonOutput []byte
	if !pd.MediaInfo.ImageID.IsEmptyID() {
		imageIdentifier := ImageIdentifier{
			ImageID: pd.MediaInfo.ImageID.String(),
			Type:    "image",
		}
		jsonOutput, err = json.Marshal(ImagePredictionOutput{
			PredictionOutput: predictionOutput,
			MediaIdentifier:  imageIdentifier,
		})
	} else if !pd.MediaInfo.VideoID.IsEmptyID() {
		videoFrameIdentifier := VideoFrameIdentifier{
			VideoID:    pd.MediaInfo.VideoID.String(),
			FrameIndex: pd.MediaInfo.FrameIndex,
			KeyIndex:   pd.MediaInfo.KeyIndex,
			Type:       "video_frame",
		}
		jsonOutput, err = json.Marshal(VideoFramePredictionOutput{
			PredictionOutput: predictionOutput,
			MediaIdentifier:  videoFrameIdentifier,
		})
	} else { // Ephemeral prediction
		jsonOutput, err = json.Marshal(predictionOutput)
	}

	if err != nil {
		return nil, err
	}

	return jsonOutput, nil
}

func (pd PredictionRequestData) ToExplainBytes(explainJSONString string) ([]byte, error) {
	var (
		explainJSON  ExplainJSON
		explainBytes = []byte(explainJSONString)
		err          error
	)
	if err := json.Unmarshal(explainBytes, &explainJSON); err != nil {
		return nil, err
	}
	explainOutput := ExplainOutput{explainJSON, GetCurrentTimeString()}
	var jsonOutput []byte
	if !pd.MediaInfo.ImageID.IsEmptyID() {
		imageIdentifier := ImageIdentifier{
			ImageID: pd.MediaInfo.ImageID.String(),
			Type:    "image",
		}
		jsonOutput, err = json.Marshal(ImageExplainOutput{
			ExplainOutput:   explainOutput,
			MediaIdentifier: imageIdentifier,
		})
	} else if !pd.MediaInfo.VideoID.IsEmptyID() {
		videoFrameIdentifier := VideoFrameIdentifier{
			VideoID:    pd.MediaInfo.VideoID.String(),
			FrameIndex: pd.MediaInfo.FrameIndex,
			Type:       "video_frame",
		}
		jsonOutput, err = json.Marshal(VideoFrameExplainOutput{
			ExplainOutput:   explainOutput,
			MediaIdentifier: videoFrameIdentifier,
		})
	} else { // Ephemeral prediction
		jsonOutput, err = json.Marshal(explainOutput)
	}

	if err != nil {
		return nil, err
	}
	return jsonOutput, nil
}

type BatchPredictionRequestData struct {
	OrganizationID  sdkentities.ID
	WorkspaceID     sdkentities.ID
	ProjectID       sdkentities.ID
	ModelID         sdkentities.ID
	Roi             Roi
	FrameSkip       int
	StartFrame      int
	EndFrame        int
	LabelOnly       bool
	MediaInfo       *MediaInfo
	HyperParameters *string
}

func (b BatchPredictionRequestData) ToSingleRequest() *PredictionRequestData {
	return &PredictionRequestData{
		OrganizationID: b.OrganizationID,
		WorkspaceID:    b.WorkspaceID,
		ProjectID:      b.ProjectID,
		ModelID:        b.ModelID,
		Roi:            b.Roi,
		MediaInfo:      *b.MediaInfo,
		UseCache:       Never,
		LabelOnly:      b.LabelOnly,
	}
}

// ExceedsMaxPredictions checks if the start frame, end frame and frame skip combination does not exceed the maximum
// amount allowed predictions
func (b BatchPredictionRequestData) ExceedsMaxPredictions(maxPredictions int) bool {
	// + 1 because start and end frame are inclusive
	numPredictions := b.EndFrame - b.StartFrame + 1
	numPredictions = numPredictions / b.FrameSkip
	return numPredictions > maxPredictions
}
