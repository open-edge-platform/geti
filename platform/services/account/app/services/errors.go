// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package services

type AlreadyExistsError struct {
	msg string
}

func NewAlreadyExistsError(msg string) *AlreadyExistsError {
	return &AlreadyExistsError{msg: msg}
}

func (e *AlreadyExistsError) Error() string {
	return e.msg
}
