// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
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
	"net/http"
)

// HTTPError represents a basic http error type with an error code, message, and status code.
type HTTPError struct {
	ErrorCode  string `json:"error_code"`  // Error code associated with the exception.
	Message    string `json:"message"`     // Error message.
	StatusCode int    `json:"http_status"` // HTTP status code associated with the exception.
}

// Error returns the status code and error message for the HTTP error, example 404: image is not found
func (e HTTPError) Error() string {
	return e.Message
}

// NewNotFoundError creates a new error that represents an HTTP 404 Not Found error with a custom message.
// It is used when a requested resource is not found in the server.
func NewNotFoundError(message string) *HTTPError {
	return &HTTPError{
		ErrorCode:  "resource_not_found",
		Message:    message,
		StatusCode: http.StatusNotFound,
	}
}

// NewInternalServerError creates a new error that represents an HTTP 500 Internal Server Error with a custom message.
// It is used when the server encounters an unexpected condition which prevents it from fulfilling the request.
// This error type should be used to signify server-side problems that are not attributable to the client.
func NewInternalServerError(message string) *HTTPError {
	return &HTTPError{
		ErrorCode:  "internal_server_error",
		Message:    message,
		StatusCode: http.StatusInternalServerError,
	}
}

// NewBadRequestError creates a new error that represents an HTTP 400 Bad Request error with a custom message. It should
// be used when the request cannot be processed due to client-side input errors.
func NewBadRequestError(message string) *HTTPError {
	return &HTTPError{
		ErrorCode:  "bad_request",
		Message:    message,
		StatusCode: http.StatusBadRequest,
	}
}

// NewNotImplementedError creates a new error that represents and HTTP 501 Not Implemented error with a custom message.
// This error should be used to indicate that the server does not support the functionality required to fulfill the request
func NewNotImplementedError(message string) *HTTPError {
	return &HTTPError{
		ErrorCode:  "not_implemented",
		Message:    message,
		StatusCode: http.StatusNotImplemented,
	}
}

// NewUnsupportedMediaType creates a new error that represents an HTTP 415 Unsupported Media Type error with a custom message.
// This error is used when the server refuses to accept the request because the payload media type is in an unsupported format.
func NewUnsupportedMediaType(message string) *HTTPError {
	return &HTTPError{
		ErrorCode:  "unsupported_media_type",
		Message:    message,
		StatusCode: http.StatusUnsupportedMediaType,
	}
}
