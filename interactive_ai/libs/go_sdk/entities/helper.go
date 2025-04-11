// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package entities

import (
	"crypto/rand"
	"fmt"
	"testing"

	"github.com/google/uuid"
)

type FullTestID struct {
	ContextID

	TestID ID
}

func getMongoLikeID(t *testing.T) string {
	randomBytes := make([]byte, 12)
	_, err := rand.Read(randomBytes)
	if err != nil {
		t.Fatalf("Cannot generate new value")
	}

	return fmt.Sprintf("%x", randomBytes)
}

func GetFullImageID(t *testing.T) *FullImageID {
	orgID := uuid.NewString()
	workspaceID := uuid.NewString()
	projectID := getMongoLikeID(t)
	datasetID := getMongoLikeID(t)
	imageID := getMongoLikeID(t)
	return NewFullImageID(orgID, workspaceID, projectID, datasetID, imageID)
}

func GetFullVideoID(t *testing.T) *FullVideoID {
	orgID := uuid.NewString()
	workspaceID := uuid.NewString()
	projectID := getMongoLikeID(t)
	datasetID := getMongoLikeID(t)
	videoID := getMongoLikeID(t)
	return NewFullVideoID(orgID, workspaceID, projectID, datasetID, videoID)
}

func GetFullTestID(t *testing.T) *FullTestID {
	return &FullTestID{
		ContextID: ContextID{
			OrganizationID: ID{uuid.NewString()},
			WorkspaceID:    ID{uuid.NewString()},
			ProjectID:      ID{getMongoLikeID(t)},
			DatasetID:      ID{getMongoLikeID(t)},
		},
		TestID: ID{getMongoLikeID(t)},
	}
}
