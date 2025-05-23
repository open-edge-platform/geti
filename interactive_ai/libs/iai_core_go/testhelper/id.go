package testhelper

import (
	"crypto/rand"
	"encoding/hex"
	"testing"

	"github.com/google/uuid"

	sdkentities "geti.com/iai_core/entities"
)

func getMongoLikeID(t *testing.T) string {
	const randomByteSize = 12
	randomBytes := make([]byte, randomByteSize)
	_, err := rand.Read(randomBytes)
	if err != nil {
		t.Fatalf("Cannot generate new value")
	}

	return hex.EncodeToString(randomBytes)
}

func GetFullImageID(t *testing.T) *sdkentities.FullImageID {
	orgID := uuid.NewString()
	workspaceID := uuid.NewString()
	projectID := getMongoLikeID(t)
	datasetID := getMongoLikeID(t)
	imageID := getMongoLikeID(t)
	return sdkentities.NewFullImageID(orgID, workspaceID, projectID, datasetID, imageID)
}
