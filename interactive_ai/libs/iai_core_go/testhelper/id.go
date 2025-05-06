package testhelper

import (
	"crypto/rand"
	"fmt"
	"testing"

	"github.com/google/uuid"

	sdkentities "geti.com/iai_core/entities"
)

func getMongoLikeID(t *testing.T) string {
	randomBytes := make([]byte, 12)
	_, err := rand.Read(randomBytes)
	if err != nil {
		t.Fatalf("Cannot generate new value")
	}

	return fmt.Sprintf("%x", randomBytes)
}

func GetFullImageID(t *testing.T) *sdkentities.FullImageID {
	orgID := uuid.NewString()
	workspaceID := uuid.NewString()
	projectID := getMongoLikeID(t)
	datasetID := getMongoLikeID(t)
	imageID := getMongoLikeID(t)
	return sdkentities.NewFullImageID(orgID, workspaceID, projectID, datasetID, imageID)
}
