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

package errors

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestHTTPErrors(t *testing.T) {
	tests := []struct {
		name           string
		constructor    func(string) *HTTPError
		wantMessage    string
		wantErrorCode  string
		wantStatusCode int
	}{
		{
			name:           "NotFoundError",
			constructor:    NewNotFoundError,
			wantMessage:    "Resource not found",
			wantErrorCode:  "resource_not_found",
			wantStatusCode: 404,
		},
		{
			name:           "InternalServerError",
			constructor:    NewInternalServerError,
			wantMessage:    "Internal server error occured",
			wantErrorCode:  "internal_server_error",
			wantStatusCode: 500,
		},
		{
			name:           "BadRequestError",
			constructor:    NewBadRequestError,
			wantMessage:    "Bad request error occured",
			wantErrorCode:  "bad_request",
			wantStatusCode: 400,
		},
		{
			name:           "NotImplementedError",
			constructor:    NewNotImplementedError,
			wantMessage:    "Not implemented",
			wantErrorCode:  "not_implemented",
			wantStatusCode: 501,
		},
		{
			name:           "UnsupportedMediaTypeError",
			constructor:    NewUnsupportedMediaType,
			wantMessage:    "Unsupported media type",
			wantErrorCode:  "unsupported_media_type",
			wantStatusCode: 415,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.constructor(tt.wantMessage)
			assert.Equal(t, tt.wantMessage, err.Message)
			assert.Equal(t, tt.wantErrorCode, err.ErrorCode)
			assert.Equal(t, tt.wantStatusCode, err.StatusCode)
			assert.Equal(t, tt.wantMessage, err.Error())
		})
	}
}
