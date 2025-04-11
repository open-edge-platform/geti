// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package models

import (
	"database/sql"
	"fmt"
	"time"

	"common/utils"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

var logger = utils.InitializeLogger()

type Organization struct {
	ID                  uuid.UUID     `gorm:"primaryKey;type:uuid;default:gen_random_uuid()"`
	Name                string        `gorm:"size:200;not null;default:null"`
	Country             string        `gorm:"size:3"`
	Location            string        `gorm:"size:200"`
	Type                string        `gorm:"size:3"`
	CellID              string        `gorm:"size:200"`
	Status              string        `gorm:"size:3;not null;default:null"`
	Logo                string        `gorm:"size:200"`
	CreatedAt           time.Time     `gorm:"autoCreateTime"`
	CreatedBy           string        `gorm:"size:200"`
	ModifiedAt          *sql.NullTime `gorm:"autoUpdateTime"`
	ModifiedBy          string        `gorm:"size:200"`
	RequestAccessReason string        `gorm:"size:5000"`
}

func (o *Organization) Create(tx *gorm.DB) error {
	result := tx.Create(o)
	if result.Error != nil {
		if ErrorIsPGUniqueViolation(result.Error, "organizations_name_key") {
			logger.Errorf("couldn't create an organization: organization %s already exists", o.ID)
			return NewAlreadyExistsError(fmt.Sprintf("organization %s already exists", o.Name))
		}
		return result.Error
	}
	return nil
}
