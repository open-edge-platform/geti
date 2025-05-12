// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
