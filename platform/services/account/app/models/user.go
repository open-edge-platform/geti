// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package models

import (
	"database/sql"
	"time"

	"github.com/google/uuid"
)

type User struct {
	ID                     uuid.UUID     `gorm:"primaryKey;type:uuid;default:gen_random_uuid()"`
	FirstName              string        `gorm:"size:200;default:null"`
	SecondName             string        `gorm:"size:200;default:null"`
	Email                  string        `gorm:"size:200;not null;default:null"`
	ExternalId             string        `gorm:"size:200"`
	PhotoLocation          string        `gorm:"size:200;unique;default:null"`
	Country                string        `gorm:"size:3;default:null"`
	RegistrationToken      string        `gorm:"size:200;unique;default:null"`
	LastSuccessfulLogin    *sql.NullTime `gorm:"default:null"`
	CurrentSuccessfulLogin *sql.NullTime `gorm:"default:null"`
	LastLogoutDate         *sql.NullTime `gorm:"default:null"`
	CreatedAt              time.Time     `gorm:"autoCreateTime"`
	CreatedBy              string        `gorm:"size:200"`
	ModifiedAt             *sql.NullTime `gorm:"autoUpdateTime"`
	ModifiedBy             string        `gorm:"size:200"`
	TelemetryConsent       *string       `gorm:"size:1;default:null"`
	TelemetryConsentAt     *sql.NullTime `gorm:"default:null"`
	UserConsent            *string       `gorm:"size:1;default:null"`
	UserConsentAt          *sql.NullTime `gorm:"default:null"`
}
