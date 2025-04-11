// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package models

import (
	"fmt"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type OrganizationStatusHistory struct {
	ID     uint   `gorm:"primaryKey;"`
	Status string `gorm:"size:3;not null;default:null"`

	OrganizationID uuid.UUID
	Organization   Organization `gorm:"foreignKey:OrganizationID;constraint:OnDelete:CASCADE;"`

	CreatedAt time.Time `gorm:"autoCreateTime"`
	CreatedBy string    `gorm:"size:200"`
}

func (h *OrganizationStatusHistory) Create(tx *gorm.DB) error {
	result := tx.Create(&h)
	if result.Error != nil {
		logger.Errorf("error during organization status history Create: %v", result.Error)
		return fmt.Errorf("error during organization status history Create: %v", result.Error)
	}
	return nil
}
