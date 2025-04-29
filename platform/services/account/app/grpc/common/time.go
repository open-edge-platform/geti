// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package common

import (
	"database/sql"
	"time"

	"github.com/golang/protobuf/ptypes/timestamp"
)

func SqlTimeToTimestamp(t *sql.NullTime) *timestamp.Timestamp {
	if t == nil || !t.Valid {
		return nil
	}
	return &timestamp.Timestamp{
		Seconds: t.Time.Unix(),
		Nanos:   int32(t.Time.Nanosecond()),
	}
}

func TimestampToSqlTime(t *timestamp.Timestamp) *sql.NullTime {
	if t == nil {
		return &sql.NullTime{Valid: false}
	}
	return &sql.NullTime{
		Valid: true,
		Time:  time.Unix(t.Seconds, int64(t.Nanos)),
	}
}
