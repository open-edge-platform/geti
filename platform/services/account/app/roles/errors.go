// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package roles

import v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"

type InvalidRoleError struct {
	msg string
}

func NewInvalidRoleError(msg string) *InvalidRoleError {
	return &InvalidRoleError{msg: msg}
}

func (e *InvalidRoleError) Error() string {
	return e.msg
}

type RoleAlreadyExistsError struct {
	msg                 string
	alreadyExistsRoleOp *v1.RelationshipUpdate
}

func NewRoleAlreadyExistsError(msg string, alreadyExistsRoleOp *v1.RelationshipUpdate) *RoleAlreadyExistsError {
	return &RoleAlreadyExistsError{msg: msg,
		alreadyExistsRoleOp: alreadyExistsRoleOp}
}

func (e *RoleAlreadyExistsError) Error() string {
	return e.msg
}
