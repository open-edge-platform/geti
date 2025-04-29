// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package models

import (
	"database/sql"
	"time"

	"github.com/google/uuid"
)

type Workspace struct {
	ID   uuid.UUID `gorm:"primaryKey;type:uuid;default:gen_random_uuid()"`
	Name string    `gorm:"size:200;not null;default:null"`

	OrganizationID uuid.UUID
	Organization   Organization `gorm:"foreignKey:OrganizationID;constraint:OnDelete:CASCADE;"`

	CreatedAt  time.Time     `gorm:"autoCreateTime"`
	CreatedBy  string        `gorm:"size:200"`
	ModifiedAt *sql.NullTime `gorm:"autoUpdateTime"`
	ModifiedBy string        `gorm:"size:200"`
}

type FindWorkspaceRequest struct {
	Name                  string
	OrganizationId        string
	BillingChildAccountId string
	CreatedAtFrom         *time.Time
	CreatedAtTo           *time.Time
	CreatedBy             string
	ModifiedAtFrom        *time.Time
	ModifiedAtTo          *time.Time
	ModifiedBy            string
	Skip                  int32
	Limit                 int32
	SortBy                string
	SortDirection         string
}