// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package entities

import "gopkg.in/validator.v2"

var emptyID = ID{""}

// ID struct
type ID struct {
	ID string `validate:"min=24,max=36,regexp=^[A-Fa-f0-9-]+$"`
}

// ContextID struct
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

// IsValid checks if the ID is a valid ObjectId or UUID
func (s ID) IsValid() error {
	return validator.Validate(s)
}

// IsEmptyID checks if the ID is empty
func (s ID) IsEmptyID() bool {
	return s == emptyID
}
