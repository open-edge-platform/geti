// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//go:build integration

package minio

import (
	"context"
	"log"
	"os"
	"testing"

	"geti.com/iai_core/testhelper"
)

func TestMain(m *testing.M) {
	ctx := context.Background()
	container, err := testhelper.StartMinioContainer(ctx)
	if err != nil {
		log.Fatalf("Cannot start minio container: %s", container)
	}

	code := m.Run()

	if err := testhelper.StopMinioContainer(ctx, container); err != nil {
		log.Fatalf("Failed to terminate container: %v", err)
	}

	os.Exit(code)
}
