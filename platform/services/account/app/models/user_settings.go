// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package models

import (
	"database/sql"
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

type UserSettings struct {
	ID uuid.UUID `gorm:"primaryKey;type:uuid;default:gen_random_uuid()"`

	OrganizationID uuid.UUID
	Organization   Organization `gorm:"foreignKey:OrganizationID;constraint:OnDelete:CASCADE;"`

	UserID uuid.UUID
	User   User `gorm:"foreignKey:UserID;constraint:OnDelete:CASCADE;"`

	ProjectID *string

	Data json.RawMessage

	CreatedAt  time.Time     `gorm:"autoCreateTime"`
	CreatedBy  string        `gorm:"size:200"`
	ModifiedAt *sql.NullTime `gorm:"autoUpdateTime"`
	ModifiedBy string        `gorm:"size:200"`
}
