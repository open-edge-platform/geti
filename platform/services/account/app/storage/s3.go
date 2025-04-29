// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package storage

import (
	"bytes"
	"context"
	"fmt"
	"time"

	"account_service/app/common/utils"
	"account_service/app/config"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsConfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

var logger = utils.InitializeLogger()

const (
	apiTimeout                   = 10 * time.Second
	presignUrlExpirationDuration = 24 * time.Hour
)

type VarCredentialProvider struct {
	AccessKeyID     string
	SecretAccessKey string
}

func (c *VarCredentialProvider) Retrieve(ctx context.Context) (aws.Credentials, error) {
	return aws.Credentials{
		AccessKeyID:     c.AccessKeyID,
		SecretAccessKey: c.SecretAccessKey,
	}, nil
}

type S3Storage struct {
	client             *s3.Client
	presignedURLClient *s3.Client
	bucket             string
}

func newS3ClientWithCustomCredsProvider(s3StorageAddress string, customCredentialsProvider aws.CredentialsProvider) (*s3.Client, error) {
	customResolver := aws.EndpointResolverWithOptionsFunc(func(service, region string, options ...interface{}) (aws.Endpoint, error) { //nolint:all (SA1019: deprecated)
		return aws.Endpoint{ //nolint:all (SA1019: deprecated)
			URL:               s3StorageAddress,
			HostnameImmutable: true,
		}, nil
	})

	sdkConfig, err := awsConfig.LoadDefaultConfig(context.Background(),
		awsConfig.WithEndpointResolverWithOptions(customResolver), //nolint:all (SA1019: deprecated)
		awsConfig.WithCredentialsProvider(customCredentialsProvider),
		awsConfig.WithRegion("auto"))
	if err != nil {
		return nil, err
	}

	return s3.NewFromConfig(sdkConfig), nil
}

func NewS3Storage(bucketName string) (*S3Storage, error) {
	storage := S3Storage{
		bucket: bucketName,
	}

	usualClient, err := newS3ClientWithCustomCredsProvider(config.S3StorageAddress, &VarCredentialProvider{
		AccessKeyID:     config.S3AccessKey,
		SecretAccessKey: config.S3SecretKey,
	})
	if err != nil {
		return nil, err
	}

	presignClient, err := newS3ClientWithCustomCredsProvider(config.S3StorageAddress, &VarCredentialProvider{
		AccessKeyID:     config.S3PresignedURLAccessKey,
		SecretAccessKey: config.S3PresignedURLSecretKey,
	})
	if err != nil {
		return nil, err
	}

	storage.client = usualClient
	storage.presignedURLClient = presignClient

	return &storage, nil
}

func (s *S3Storage) PutObject(imageData bytes.Buffer, filename string) (string, error) {
	ctx, cancelFn := context.WithTimeout(context.Background(), apiTimeout)
	defer cancelFn()

	_, err := s.client.PutObject(ctx, &s3.PutObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(filename),
		Body:   bytes.NewReader(imageData.Bytes()),
	})
	if err != nil {
		logger.Errorf("unknown error when PutObject: %v , err: %v", filename, err)
		return "", err
	}

	newLocation := fmt.Sprintf("%s/%s", s.bucket, filename)

	logger.Debugf("successfully uploaded file to %v", newLocation)
	return newLocation, nil
}

func (s *S3Storage) DeleteObject(filename string) error {
	ctx, cancelFn := context.WithTimeout(context.Background(), apiTimeout)
	defer cancelFn()

	_, err := s.client.DeleteObject(ctx, &s3.DeleteObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(filename),
	})
	if err != nil {
		logger.Errorf("unknown error when DeleteObjectWithContext: %v , err: %v", filename, err)
		return err
	}

	logger.Debugf("successfully deleted file %s/%s\n", s.bucket, filename)
	return nil
}

func (s *S3Storage) GetPresignedUrl(filename string) (string, error) {
	ctx, cancelFn := context.WithTimeout(context.Background(), apiTimeout)
	defer cancelFn()

	presignClient := s3.NewPresignClient(s.presignedURLClient)
	request, err := presignClient.PresignGetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(filename),
	}, func(opts *s3.PresignOptions) {
		opts.Expires = presignUrlExpirationDuration
	})
	if err != nil {
		logger.Errorf("failed to sign request for file: %v , err: %v", filename, err)
		return "", err
	}

	return request.URL, nil
}
