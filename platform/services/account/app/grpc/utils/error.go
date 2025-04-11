// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"strings"

	"github.com/jackc/pgx/v5/pgconn"
)

const pgUniqueViolationErrorCode = "23505"

func ErrorIsPGUniqueViolation(err error, violatedFieldDiscriminator string) bool {
	pgErr, ok := err.(*pgconn.PgError)
	if ok {
		return pgErr.Code == pgUniqueViolationErrorCode && strings.Contains(pgErr.Message, violatedFieldDiscriminator)
	}
	return false
}
