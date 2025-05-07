// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package testhelper

import (
	"context"
	"fmt"
	"os"

	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"
)

const (
	minioAccessKey      = "minioadmin"
	minioSecretKey      = "minioadmin"
	credentialsProvider = "local"
)

func StartMinioContainer(ctx context.Context) (testcontainers.Container, error) {
	req := testcontainers.ContainerRequest{
		Image:        "minio/minio",
		Cmd:          []string{"server", "/data"},
		ExposedPorts: []string{"9000/tcp"},
		Env: map[string]string{
			"MINIO_ACCESS_KEY": minioAccessKey,
			"MINIO_SECRET_KEY": minioSecretKey,
		},
		WaitingFor: wait.ForListeningPort("9000/tcp"),
	}

	minioContainer, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: req,
		Started:          true,
	})
	if err != nil {
		return minioContainer, fmt.Errorf("failed to get container host: %s", err)
	}

	endpoint, err := minioContainer.Endpoint(ctx, "")
	if err != nil {
		return minioContainer, fmt.Errorf("failed to get container endpoint: %s", err)
	}

	_ = os.Setenv("S3_CREDENTIALS_PROVIDER", credentialsProvider)
	_ = os.Setenv("S3_HOST", endpoint)
	_ = os.Setenv("S3_ACCESS_KEY", minioAccessKey)
	_ = os.Setenv("S3_SECRET_KEY", minioSecretKey)

	return minioContainer, nil
}

func StopMinioContainer(ctx context.Context, container testcontainers.Container) error {
	defer func() {
		_ = os.Unsetenv("S3_CREDENTIALS_PROVIDER")
		_ = os.Unsetenv("S3_HOST")
		_ = os.Unsetenv("S3_ACCESS_KEY")
		_ = os.Unsetenv("S3_SECRET_KEY")
	}()

	if err := container.Terminate(ctx); err != nil {
		return err
	}
	return nil
}
