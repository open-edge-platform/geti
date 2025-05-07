// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package service

import (
	"context"
	"errors"
	"testing"

	"inference_gateway/app/entities"

	"github.com/go-resty/resty/v2"
	"github.com/jarcoal/httpmock"
	"github.com/stretchr/testify/assert"

	sdk_endities "geti.com/iai_core/entities"
)

func TestPredictionCacheService(t *testing.T) {
	ctx := context.Background()
	client := resty.New()
	httpmock.ActivateNonDefault(client.GetClient())
	defer httpmock.DeactivateAndReset()
	testID := sdk_endities.GetFullTestID(t)
	req := &entities.PredictionRequestData{
		UseCache:       entities.Auto,
		OrganizationID: testID.OrganizationID,
		WorkspaceID:    testID.WorkspaceID,
		ProjectID:      testID.ProjectID,
		ModelID:        testID.TestID,
		MediaInfo:      entities.MediaInfo{DatasetID: testID.TestID, ImageID: testID.TestID},
	}
	baseURL := "http://impt-director.impt:4999"

	tests := []struct {
		name        string
		setupClient func()
		wantAsserts func(int, []byte, bool)
	}{
		{
			name: "Cached",
			setupClient: func() {
				httpmock.RegisterResponder("GET", baseURL+req.GetURL(),
					httpmock.NewStringResponder(200, `{"predictions": [{"score": 0.6}]}`))
			},
			wantAsserts: func(statusCode int, body []byte, cached bool) {
				assert.Equal(t, statusCode, 200)
				assert.Equal(t, body, []byte(`{"predictions": [{"score": 0.6}]}`))
				assert.True(t, cached)
				httpmock.Reset()
			},
		},
		{
			name: "NotCached",
			setupClient: func() {
				httpmock.RegisterResponder("GET", baseURL+req.GetURL(),
					httpmock.NewStringResponder(404, `not_found`))
			},
			wantAsserts: func(statusCode int, body []byte, cached bool) {
				assert.Equal(t, statusCode, 0)
				assert.Nil(t, body)
				assert.False(t, cached)
			},
		},
		{
			name: "ErrHTTP",
			setupClient: func() {
				httpmock.RegisterResponder("GET", baseURL+req.GetURL(),
					httpmock.NewErrorResponder(errors.New("error")))
			},
			wantAsserts: func(statusCode int, body []byte, cached bool) {
				assert.Equal(t, statusCode, 0)
				assert.Nil(t, body)
				assert.False(t, cached)
			},
		},
		{
			name: "ModeNotSupported",
			setupClient: func() {
				req.UseCache = entities.Never
			},
			wantAsserts: func(statusCode int, body []byte, cached bool) {
				assert.Equal(t, statusCode, 0)
				assert.Nil(t, body)
				assert.False(t, cached)
			},
		},
		{
			name: "ROI",
			setupClient: func() {
				req.UseCache = entities.Auto
				req.Roi = entities.Roi{
					X: 10, Y: 10, Width: 30, Height: 30,
				}
			},
			wantAsserts: func(statusCode int, body []byte, cached bool) {
				assert.Equal(t, statusCode, 0)
				assert.Nil(t, body)
				assert.False(t, cached)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(_ *testing.T) {
			tt.setupClient()
			service, err := NewPredictionCacheService(client)
			assert.NoError(t, err)

			statusCode, body, cached := service.Get(ctx, req)
			tt.wantAsserts(statusCode, body, cached)
		})
	}
}
