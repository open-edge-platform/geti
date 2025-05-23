// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//nolint:gochecknoglobals // consider refactoring global variables
package minio

import (
	"context"
	"fmt"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"github.com/caarlos0/env/v11"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"

	"geti.com/iai_core/logger"
)

type CommonConfig struct {
	CacheTTL int `env:"S3_CLIENT_CACHE_TTL" envDefault:"3600"`
}

type onPremConfig struct {
	CommonConfig

	Endpoint    string `env:"S3_HOST,notEmpty"`
	AccessKeyID string `env:"S3_ACCESS_KEY,notEmpty"`
	SecretKey   string `env:"S3_SECRET_KEY,notEmpty"`
}

type awsConfig struct {
	CommonConfig

	Region            string `env:"AWS_REGION,notEmpty"`
	IdentityTokenFile string `env:"AWS_WEB_IDENTITY_TOKEN_FILE,notEmpty"`
	Role              string `env:"AWS_ROLE_ARN,notEmpty"`
}

const (
	healthcheckIntervalSeconds = 1
	local                      = "local"
	aws                        = "aws"
)

var (
	initialized atomic.Bool
	mu          sync.Mutex
	client      *minio.Client
	hcCancelFn  context.CancelFunc
)

// Reset the minio client and stop its health check routine.
func reset() {
	mu.Lock()
	defer mu.Unlock()
	if hcCancelFn != nil {
		hcCancelFn()
		hcCancelFn = nil
	}
	initialized.Store(false)
	client = nil
}

func backgroundCheck(ctx context.Context, s3ClientCacheTTL int) {
	timer := time.NewTimer(time.Duration(s3ClientCacheTTL) * time.Second)
	defer timer.Stop()
	<-timer.C

	logger.TracingLog(ctx).Infof("S3 Client Cache TTL has expired. Resetting the minio client...")
	reset()
}

// getMinioClient returns a minio client based on the value of the S3_CREDENTIALS_PROVIDER environment variable.
// If the value is "local", it calls newOnPremMinioClient function, otherwise it calls newAWSMinioClient function.
// If the value of S3_CREDENTIALS_PROVIDER is neither "aws" nor "local", it returns an error.
func getMinioClient(ctx context.Context) (*minio.Client, error) {
	provider := os.Getenv("S3_CREDENTIALS_PROVIDER")
	if provider != local && provider != aws {
		const msg = "unsupported environment variable S3_CREDENTIALS_PROVIDER: found %s but the value should either be 'aws' or 'local'"
		return nil, fmt.Errorf(msg, os.Getenv("S3_CREDENTIALS_PROVIDER"))
	}
	if initialized.Load() {
		return client, nil
	}
	mu.Lock()
	defer mu.Unlock()
	if !initialized.Load() {
		var (
			minioClient *minio.Client
			cacheTTL    int
			err         error
		)
		if provider == local {
			minioClient, cacheTTL, err = newOnPremMinioClient(ctx)
		} else {
			minioClient, cacheTTL, err = newAWSMinioClient(ctx)
		}
		if err != nil {
			return nil, err
		}

		// Check health of minio client every second
		hcCancel, healthErr := minioClient.HealthCheck(healthcheckIntervalSeconds * time.Second)
		if healthErr != nil {
			return nil, healthErr
		}

		client = minioClient
		hcCancelFn = hcCancel
		initialized.Store(true)
		go backgroundCheck(ctx, cacheTTL)
	}
	return client, nil
}

func newOnPremMinioClient(ctx context.Context) (*minio.Client, int, error) {
	logger.TracingLog(ctx).Infof("Initializing on-prem minio client.")
	cfg := onPremConfig{}
	if err := env.Parse(&cfg); err != nil {
		return nil, 0, err
	}

	// Initialize minio client object.
	minioClient, err := minio.New(cfg.Endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(cfg.AccessKeyID, cfg.SecretKey, ""),
		Secure: false,
	})
	return minioClient, cfg.CacheTTL, err
}

func newAWSMinioClient(ctx context.Context) (*minio.Client, int, error) {
	logger.TracingLog(ctx).Infof("Initializing saas minio client.")
	cfg := awsConfig{}
	if err := env.Parse(&cfg); err != nil {
		return nil, 0, err
	}
	creds, err := credentials.NewIAM("").Get()
	if err != nil {
		return nil, 0, err
	}

	// Initialize minio client object.
	minioClient, err := minio.New("s3.amazonaws.com", &minio.Options{
		Creds:  credentials.NewStaticV4(creds.AccessKeyID, creds.SecretAccessKey, creds.SessionToken),
		Secure: true,
		Region: cfg.Region,
	})
	return minioClient, cfg.CacheTTL, err
}
