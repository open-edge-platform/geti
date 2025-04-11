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

package usecase

import (
	"context"
	"fmt"
	"testing"

	sdkentities "geti.com/go_sdk/entities"
	mockframes "geti.com/go_sdk/mock/frames"
	mockstorage "geti.com/go_sdk/mock/storage"
	pb "geti.com/predict"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	"inference_gateway/app/entities"
	mockservice "inference_gateway/app/mock/service"
)

func TestExplainBatch(t *testing.T) {

	ctx := context.Background()
	fullVideoID := sdkentities.GetFullVideoID(t)
	start, end, skip := 0, 199, 10
	total := (end-start)/skip + 1
	video := &sdkentities.Video{FilePath: "video_path", FPS: 25}
	// Prepare test variables
	mediaInfo := entities.MediaInfo{
		VideoID:   fullVideoID.VideoID,
		DatasetID: fullVideoID.DatasetID,
	}
	hyperParamaters := "{'confidence_treshold':0.35}"
	batchRequest := entities.BatchPredictionRequestData{
		OrganizationID:  fullVideoID.OrganizationID,
		WorkspaceID:     fullVideoID.WorkspaceID,
		ProjectID:       fullVideoID.ProjectID,
		ModelID:         sdkentities.ID{ID: "000000000000000000000003"},
		MediaInfo:       &mediaInfo,
		StartFrame:      start,
		EndFrame:        end,
		FrameSkip:       skip,
		HyperParameters: &hyperParamaters,
	}

	mockModelAccess := mockservice.NewMockModelAccessService(t)
	mockVideoRepo := mockstorage.NewMockVideoRepository(t)
	mockFrameExtractor := mockframes.NewMockCLIFrameExtractor(t)

	mockVideoRepo.EXPECT().
		LoadVideoByID(ctx, fullVideoID).
		Return(video, nil).
		Once()
	mockFrameExtractor.EXPECT().
		Start(mock.AnythingOfType("*context.valueCtx"), video, start, end, skip, mock.AnythingOfType("*io.PipeWriter")).
		Return(MockDoneCh())
	mockFrameExtractor.EXPECT().
		Read(mock.AnythingOfType("*context.valueCtx"), mock.AnythingOfType("*io.PipeReader")).
		Return(MockFrameCh(total))

	respParams := map[string]*pb.InferParameter{"predictions": {
		ParameterChoice: &pb.InferParameter_StringParam{StringParam: `{"score": 0.7}`}}}
	inferResp := &pb.ModelInferResponse{Parameters: respParams}
	mockModelAccess.EXPECT().
		InferImageBytes(mock.AnythingOfType("*context.cancelCtx"), mock.AnythingOfType("InferParameters")).
		Return(inferResp, nil).
		Times(total)

	infer := NewExplain(mockModelAccess, mockVideoRepo, mockFrameExtractor)
	result, err := infer.Batch(ctx, &batchRequest)
	assert.NoError(t, err)
	assert.NotNil(t, result)
	assert.Len(t, result.BatchExplain, total)
	for i, item := range result.BatchExplain {
		assert.NotNil(t, item)
		assert.Contains(t, string(item), "maps")
		assert.Contains(t, string(item), fmt.Sprintf("\"frame_index\":%d", i*skip))
	}
}
