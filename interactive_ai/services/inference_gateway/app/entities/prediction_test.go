// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import (
	"bytes"
	"fmt"
	"image"
	"image/draw"
	"image/jpeg"
	"regexp"
	"testing"

	sdkentities "geti.com/iai_core/entities"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	testhelpers "inference_gateway/app/test_helpers"
)

// Instantiate dummy entities for test purposes.
func CreateDummyPredictionEntities(t *testing.T) (image.Image, *MediaInfo, PredictionRequestData) {
	t.Helper()

	img := testhelpers.GetUniformTestImage(500, 250, uint8(100))

	buf := new(bytes.Buffer)
	err := jpeg.Encode(buf, img, nil)
	require.NoError(t, err)

	m := MediaInfo{
		ImageID:    testhelpers.NewDummyID(5),
		VideoID:    testhelpers.NewDummyID(6),
		FrameIndex: 0,
		DatasetID:  testhelpers.NewDummyID(7),
	}

	p := PredictionRequestData{
		OrganizationID: testhelpers.NewDummyID(1),
		WorkspaceID:    testhelpers.NewDummyID(2),
		ProjectID:      testhelpers.NewDummyID(3),
		ModelID:        testhelpers.NewDummyID(4),
		Media:          buf,
		Roi:            Roi{},
		UseCache:       Always,
		LabelOnly:      false,
		MediaInfo:      m,
	}
	return img, &m, p
}

func TestDecodeMedia(t *testing.T) {
	img, _, predictionRequestData := CreateDummyPredictionEntities(t)

	decodedImage, err := predictionRequestData.DecodeMedia()

	require.NoError(t, err)

	// Convert the decodedImage to RGBA to be able to compare with the original
	b := decodedImage.Bounds()
	m := image.NewRGBA(image.Rect(0, 0, b.Dx(), b.Dy()))
	draw.Draw(m, m.Bounds(), decodedImage, b.Min, draw.Src)
	assert.Equal(t, img, m)
}

func TestExceedsMaxPredictions(t *testing.T) {
	batchPredRequestData := BatchPredictionRequestData{
		StartFrame: 1,
		EndFrame:   10,
		FrameSkip:  1,
	}
	assert.False(t, batchPredRequestData.ExceedsMaxPredictions(10))
	assert.True(t, batchPredRequestData.ExceedsMaxPredictions(9))
}

func TestPredictionRequestData_ToPredictBytes(t *testing.T) {
	var (
		predictionRequestData PredictionRequestData
		mediaInfo             MediaInfo
	)
	mediaInfo.ImageID = sdkentities.ID{ID: "123456789012345678901234"}
	predictionRequestData.MediaInfo = mediaInfo

	predictionString := `{"predictions":{"key1":"value1","key2":2},"maps":{"key3":"value3","key4":4}}`
	expectedPattern := regexp.MustCompile(
		fmt.Sprintf(
			`{"predictions":{"key1":"value1","key2":2},"created":"[^"]+","media_identifier":{"image_id":"%s","type":"image"}}`,
			regexp.QuoteMeta(mediaInfo.ImageID.String()),
		),
	)
	output, err := predictionRequestData.ToPredictBytes(predictionString)
	require.NoError(t, err)
	assert.Regexp(t, expectedPattern, string(output))
}

func TestPredictionRequestData_ToExplainBytes(t *testing.T) {
	var (
		predictionRequestData PredictionRequestData
		mediaInfo             MediaInfo
	)
	mediaInfo.ImageID = sdkentities.ID{ID: "123456789012345678901234"}
	predictionRequestData.MediaInfo = mediaInfo

	predictionString := `{"predictions":{"key1":"value1","key2":2},"maps":{"key3":"value3","key4":4}}`
	expectedPattern := regexp.MustCompile(
		fmt.Sprintf(
			`{"maps":{"key3":"value3","key4":4},"created":"[^"]+","media_identifier":{"image_id":"%s","type":"image"}}`,
			regexp.QuoteMeta(mediaInfo.ImageID.String()),
		),
	)
	output, err := predictionRequestData.ToExplainBytes(predictionString)
	require.NoError(t, err)
	assert.Regexp(t, expectedPattern, string(output))
}
