// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package models

import (
	"strings"

	"github.com/jackc/pgx/v5/pgconn"
)

const pgUniqueViolationErrorCode = "23505"

type AlreadyExistsError struct {
	msg string
}

func NewAlreadyExistsError(msg string) *AlreadyExistsError {
	return &AlreadyExistsError{msg: msg}
}

func (e *AlreadyExistsError) Error() string {
	return e.msg
}

func ErrorIsPGUniqueViolation(err error, violatedFieldDiscriminator string) bool {
	pgErr, ok := err.(*pgconn.PgError)
	if ok {
		return pgErr.Code == pgUniqueViolationErrorCode && strings.Contains(pgErr.Message, violatedFieldDiscriminator)
	}
	return false
}
