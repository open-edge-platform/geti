// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package models

import (
	"database/sql"
	"time"

	"github.com/google/uuid"
)

type PersonalAccessToken struct {
	Hash        string    `gorm:"size:65;not null;default:null"`
	ID          uuid.UUID `gorm:"primaryKey;type:uuid;default:gen_random_uuid()"`
	Partial     string    `gorm:"size:36;not null;default:null"`
	Name        string    `gorm:"size:100;not null;default:null"`
	Description string    `gorm:"size:1000;default:null"`
	ExpiresAt   time.Time
	Status      string `gorm:"size:3;not null;default:null"`

	UserID uuid.UUID
	User   User `gorm:"foreignKey:UserID;constraint:OnDelete:CASCADE;"`

	OrganizationID uuid.UUID
	Organization   Organization `gorm:"foreignKey:OrganizationID;constraint:OnDelete:CASCADE;"`

	CreatedAt  time.Time     `gorm:"autoCreateTime"`
	CreatedBy  string        `gorm:"size:200"`
	ModifiedAt *sql.NullTime `gorm:"autoUpdateTime"`
	ModifiedBy string        `gorm:"size:200"`
}
