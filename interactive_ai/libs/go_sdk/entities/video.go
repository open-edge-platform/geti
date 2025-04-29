// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"context"
	"encoding/json"
	"math"
	"path/filepath"
	"strconv"
	"strings"

	ffmpeg "github.com/u2takey/ffmpeg-go"
	"go.opentelemetry.io/otel/codes"

	"geti.com/go_sdk/logger"
	"geti.com/go_sdk/telemetry"
)

// FullVideoID represents full path to the video
type FullVideoID struct {
	ContextID

	VideoID ID
}

// VideoInfo captures metadata from ffprobe result to identify fps of a video stream
type VideoInfo struct {
	Streams []struct {
		CodecType  string `json:"codec_type"`
		RFrameRate string `json:"r_frame_rate"`
	} `json:"streams"`
}

// NewFullVideoID creates new full video id struct
func NewFullVideoID(organizationID string, workspaceID string, projectID string, datasetID string, videoID string) *FullVideoID {
	return &FullVideoID{
		ContextID: ContextID{
			OrganizationID: ID{organizationID},
			WorkspaceID:    ID{workspaceID},
			ProjectID:      ID{projectID},
			DatasetID:      ID{datasetID},
		},
		VideoID: ID{videoID},
	}
}

// GetPath construct the path to the video based on IDs
func (vid FullVideoID) GetPath() string {
	return filepath.Join("organizations", vid.OrganizationID.String(), "workspaces", vid.WorkspaceID.String(), "projects",
		vid.ProjectID.String(), "dataset_storages", vid.DatasetID.String(), vid.VideoID.String())
}

// Video represents video metadata.
type Video struct {
	FilePath string
	FPS      float64
}

func NewVideo(ctx context.Context, filepath string) *Video {
	return &Video{
		FilePath: filepath,
		FPS:      GetFPS(ctx, filepath),
	}
}

// GetFPS uses ffprobe to return video FPS rate.
// Returns 0, if FPS cannot be determined.
func GetFPS(ctx context.Context, path string) float64 {
	c, span := telemetry.Tracer().Start(ctx, "get-fps-ffprobe")
	defer span.End()
	data, err := ffmpeg.Probe(path)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		logger.TracingLog(c).Infof("Error getting fps from video %q using ffprobe", path)
		return 0
	}
	vInfo := &VideoInfo{}
	err = json.Unmarshal([]byte(data), vInfo)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		logger.TracingLog(c).Infof("Cannot convert ffprobe result to JSON: %s", data)
		return 0
	}
	for _, s := range vInfo.Streams {
		if s.CodecType == "video" {
			fps := parseFPSFraction(s.RFrameRate)
			logger.TracingLog(c).Infof("Video fps successfully identified: %g", fps)
			return fps
		}
	}

	return 0
}

// parseFPSFraction converts an ffprobe r_frame_rate value (e.g., "30000/1001")
// to a float representing frames per second (FPS), rounded to two decimal places.
// Example input: "30000/1001", resulting in an output: 29.97.
func parseFPSFraction(fpsFraction string) float64 {
	nums := strings.Split(fpsFraction, "/")
	n, err := strconv.ParseFloat(nums[0], 32)
	if err != nil {
		return 0
	}
	d, err := strconv.ParseFloat(nums[1], 32)
	if err != nil {
		return 0
	}
	fps := math.Round(n/d*100) / 100
	return fps
}
