// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

import "gopkg.in/validator.v2"

// ID struct.
type ID struct {
	ID string `validate:"min=24,max=36,regexp=^[A-Fa-f0-9-]+$"`
}

// ContextID struct.
type ContextID struct {
	OrganizationID ID
	WorkspaceID    ID
	ProjectID      ID
	DatasetID      ID
}

// String function of ID.
func (s ID) String() string {
	return s.ID
}

// IsValid checks if the ID is a valid ObjectId or UUID.
func (s ID) IsValid() error {
	return validator.Validate(s)
}

// IsEmptyID checks if the ID is empty.
func (s ID) IsEmptyID() bool {
	return s == ID{""}
}
