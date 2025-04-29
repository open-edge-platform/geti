// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package models

import (
	"time"

	"github.com/google/uuid"
)

type UserStatus struct {
	ID     uuid.UUID `gorm:"primaryKey;type:uuid;default:gen_random_uuid()"`
	Status string    `gorm:"size:3;not null;default:null"`

	OrganizationName string `gorm:"size:200"`
	OrganizationID   uuid.UUID
	Organization     Organization `gorm:"foreignKey:OrganizationID;constraint:OnDelete:CASCADE;"`

	UserID uuid.UUID
	User   User `gorm:"foreignKey:UserID;constraint:OnDelete:CASCADE;"`

	Current bool

	CreatedAt time.Time `gorm:"autoCreateTime"`
	CreatedBy string    `gorm:"size:200"`
}

type MembershipResult struct {
	ID         uuid.UUID `gorm:"type:uuid"`
	UserID     uuid.UUID `gorm:"type:uuid"`
	FirstName  string
	SecondName string
	Email      string
	Status     string
	CreatedAt  time.Time
}

type UserMembershipResult struct {
	ID               uuid.UUID `gorm:"type:uuid"`
	OrganizationID   uuid.UUID `gorm:"type:uuid"`
	OrganizationName string
	Status           string
	CreatedAt        time.Time
}
