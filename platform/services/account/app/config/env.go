// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package config

import (
	"fmt"

	"common/utils"
)

const (
	grpcServerPortEnvVarName    = "GRPC_SERVER_PORT"
	grpcServerDefaultPort       = 5001
	GatewayServerPortEnvVarName = "GATEWAY_SERVER_PORT"
	GatewayServerDefaultPort    = 5002

	dbHostEnvVarName        = "POSTGRES_HOST"
	dbUserEnvVarName        = "POSTGRES_USER"
	dbPasswordEnvVarName    = "POSTGRES_PASSWORD"
	dbPortEnvVarName        = "POSTGRES_PORT"
	dbDBNameEnvVarName      = "POSTGRES_DB_NAME"
	dbSSLModeEnvVarName     = "POSTGRES_SSLMODE"
	dbSSLRootCertEnvVarName = "AWS_BUNDLE_PATH"

	dbSSLModeDefault = "disable"

	s3StorageAddressEnvVarName = "S3_ENDPOINT"
	s3StorageAddressDefault    = "http://127.0.0.1:8333"

	s3AccessKeyEnvVarName = "S3_ACCESS_KEY"
	s3SecretKeyEnvVarName = "S3_SECRET_KEY"

	s3PresignedURLAccessKeyEnvVarName = "S3_PRESIGNED_URL_ACCESS_KEY"
	s3PresignedURLSecretKeyEnvVarName = "S3_PRESIGNED_URL_SECRET_KEY"

	s3KeysDefault = "any"

	s3OrganizationLogosBucketNameEnvVarName = "S3_ORGANIZATION_LOGOS_BUCKET_NAME"
	s3OrganizationLogosBucketNameDefault    = "logos"
	s3UserPhotosBucketNameEnvVarName        = "S3_USER_PHOTOS_BUCKET_NAME"
	s3UserPhotosBucketNameDefault           = "userphotos"

	spiceDBAddressEnvVarName = "SPICEDB_ADDRESS"
	spiceDBAddressDefault    = "127.0.0.1:50051"
	spiceDBTokenEnvVarName   = "SPICEDB_TOKEN"
	spiceDBTokenDefault      = "somerandomkeyhere"

	otelEnableMetricsEnvVarName   = "ENABLE_METRICS"
	otelServiceNameEnvVarName     = "OTEL_SERVICE_NAME"
	otelMetricsReceiverEnvVarName = "OTLP_METRICS_RECEIVER"

	kafkaAddressEnvVarName                             = "KAFKA_ADDRESS"
	kafkaUsernameEnvVarName                            = "KAFKA_USERNAME"
	kafkaPasswordEnvVarName                            = "KAFKA_PASSWORD"
	kafkaTopicPrefixEnvVarName                         = "KAFKA_TOPIC_PREFIX"
	kafkaSecurityProtocolEnvVarName                    = "KAFKA_SECURITY_PROTOCOL"
	getiNotificationTopicEnvVarName                    = "GETI_NOTIFICATION_TOPIC"
	getiNotificationTopicDefault                       = "geti"
	invitationFromAddressEnvVarName                    = "INVITATION_FROM_ADDRESS"
	invitationFromAddressDefault                       = "notification@geti.com"
	invitationFromNameEnvVarName                       = "INVITATION_FROM_NAME"
	invitationFromNameDefault                          = "Geti Admin"
	userInvitationMailMessageEnvVarName                = "USER_INVITATION_MAIL_MESSAGE"
	userInvitationMailTopicEnvVarName                  = "USER_INVITATION_MAIL_TOPIC"
	organizationAcceptRequestedAccessMessageEnvVarName = "ORGANIZATION_ACCEPT_REQUEST_MESSAGE"
	organizationAcceptRequestedAccessTopicEnvVarName   = "ORGANIZATION_ACCEPT_REQUEST_TOPIC"
	organizationRejectRequestedAccessMessageEnvVarName = "ORGANIZATION_REJECT_REQUEST_MESSAGE"
	organizationRejectRequestedAccessTopicEnvVarName   = "ORGANIZATION_REJECT_REQUEST_TOPIC"
	organizationInvitationMailMessageEnvVarName        = "ORGANIZATION_INVITATION_MAIL_MESSAGE"
	organizationInvitationTopicEnvVarName              = "ORGANIZATION_INVITATION_TOPIC"
	defaultInvitationMailTopic                         = "You have been invited to join Intel® Geti™"
	defaultInvitationMailMessage                       = "You have been invited to join Intel® Geti™: {{ .InvitationLink }}"
	invitationLinkEnvVarName                           = "INVITATION_LINK"
	invitationLinkDefault                              = "https://geti.com/invitation_link"

	usersPerOrgLimitEnvVarName = "USERS_PER_ORG_LIMIT"
	usersPerOrgLimitDefault    = -1

	defaultWorkspaceNameEnvVarName = "DEFAULT_WORKSPACE_NAME"
	defaultWorkspaceNameDefault    = "Default workspace"

	sslCertificatesDirEnvVarName = "SPICEDB_SSL_CERTIFICATES_DIR"

	featureFlagOrgQuotasEnvVarName = "FEATURE_FLAG_ORG_QUOTAS"
	featureFlagDefaultValue        = false

	featureFlagManageUsers      = "FEATURE_FLAG_MANAGE_USERS"
	featureFlagManageUsersRoles = "FEATURE_FLAG_MANAGE_USERS_ROLES"
	featureFlagAccSvcMod        = "FEATURE_FLAG_ACC_SVC_MOD"
	featureFlagReqAccess        = "FEATURE_FLAG_REQ_ACCESS"
)

//goland:noinspection GoCommentStart
var (
	// GRPC server
	grpcServerPort    = utils.GetIntEnvOrDefault(grpcServerPortEnvVarName, grpcServerDefaultPort)
	GrpcServerAddress = fmt.Sprintf(":%v", grpcServerPort)

	// GRPC-gateway server
	gatewayServerPort        = utils.GetIntEnvOrDefault(GatewayServerPortEnvVarName, GatewayServerDefaultPort)
	GRPCGatewayServerAddress = fmt.Sprintf(":%v", gatewayServerPort)

	// postgres
	DBHost         = utils.GetStringEnvOrDefault(dbHostEnvVarName, "localhost")
	DBUser         = utils.GetStringEnvOrDefault(dbUserEnvVarName, "postgres")
	DBPassword     = utils.GetStringEnvOrDefault(dbPasswordEnvVarName, "postgres")
	DBDatabaseName = utils.GetStringEnvOrDefault(dbDBNameEnvVarName, "accsvc")
	DBPort         = utils.GetStringEnvOrDefault(dbPortEnvVarName, "5432")
	DBSSLMode      = utils.GetStringEnvOrDefault(dbSSLModeEnvVarName, dbSSLModeDefault)
	DBSSLRootCert  = utils.GetStringEnvOrDefault(dbSSLRootCertEnvVarName, "")

	// S3 storage
	S3StorageAddress = utils.GetStringEnvOrDefault(s3StorageAddressEnvVarName, s3StorageAddressDefault)

	S3AccessKey             = utils.GetStringEnvOrDefault(s3AccessKeyEnvVarName, s3KeysDefault)
	S3SecretKey             = utils.GetStringEnvOrDefault(s3SecretKeyEnvVarName, s3KeysDefault)
	S3PresignedURLAccessKey = utils.GetStringEnvOrDefault(s3PresignedURLAccessKeyEnvVarName, s3KeysDefault)
	S3PresignedURLSecretKey = utils.GetStringEnvOrDefault(s3PresignedURLSecretKeyEnvVarName, s3KeysDefault)

	S3OrganizationsLogosBucketName = utils.GetStringEnvOrDefault(s3OrganizationLogosBucketNameEnvVarName, s3OrganizationLogosBucketNameDefault)
	S3UserPhotosBucketName         = utils.GetStringEnvOrDefault(s3UserPhotosBucketNameEnvVarName, s3UserPhotosBucketNameDefault)

	// spicedb
	SpiceDBAddress = utils.GetStringEnvOrDefault(spiceDBAddressEnvVarName, spiceDBAddressDefault)
	SpiceDBToken   = utils.GetStringEnvOrDefault(spiceDBTokenEnvVarName, spiceDBTokenDefault)

	// OTEL
	OtelEnableMetrics   = utils.GetBoolEnvOrDefault(otelEnableMetricsEnvVarName, false)
	OtelServiceName     = utils.GetStringEnvOrDefault(otelServiceNameEnvVarName, "account-service")
	OtelMetricsReceiver = utils.GetStringEnvOrDefault(otelMetricsReceiverEnvVarName, "localhost")

	// invitation
	KafkaAddress          = utils.GetStringEnvOrDefault(kafkaAddressEnvVarName, "127.0.0.1:9092")
	KafkaUsername         = utils.GetStringEnvOrDefault(kafkaUsernameEnvVarName, "")
	KafkaPassword         = utils.GetStringEnvOrDefault(kafkaPasswordEnvVarName, "")
	KafkaTopicPrefix      = utils.GetStringEnvOrDefault(kafkaTopicPrefixEnvVarName, "")
	KafkaSecurityProtocol = utils.GetStringEnvOrDefault(kafkaSecurityProtocolEnvVarName, "SASL_PLAINTEXT")

	GetiNotificationTopic = utils.GetStringEnvOrDefault(getiNotificationTopicEnvVarName, getiNotificationTopicDefault)
	InvitationFromAddress = utils.GetStringEnvOrDefault(invitationFromAddressEnvVarName, invitationFromAddressDefault)
	InvitationFromName    = utils.GetStringEnvOrDefault(invitationFromNameEnvVarName, invitationFromNameDefault)

	InvitationLink = utils.GetStringEnvOrDefault(invitationLinkEnvVarName, invitationLinkDefault)

	UsersPerOrgLimit = utils.GetIntEnvOrDefault(usersPerOrgLimitEnvVarName, usersPerOrgLimitDefault)

	UserInvitationMailMessage = utils.GetStringEnvOrDefault(userInvitationMailMessageEnvVarName, defaultInvitationMailMessage)
	UserInvitationMailTopic   = utils.GetStringEnvOrDefault(userInvitationMailTopicEnvVarName, defaultInvitationMailTopic)

	OrganizationInvitationMailMessage = utils.GetStringEnvOrDefault(organizationInvitationMailMessageEnvVarName, defaultInvitationMailMessage)
	OrganizationInvitationTopic       = utils.GetStringEnvOrDefault(organizationInvitationTopicEnvVarName, defaultInvitationMailTopic)

	OrganizationAcceptRequestedAccessMessage = utils.GetStringEnvOrDefault(organizationAcceptRequestedAccessMessageEnvVarName, defaultInvitationMailMessage)
	OrganizationAcceptRequestedAccessTopic   = utils.GetStringEnvOrDefault(organizationAcceptRequestedAccessTopicEnvVarName, defaultInvitationMailTopic)

	OrganizationRejectRequestedAccessMessage = utils.GetStringEnvOrDefault(organizationRejectRequestedAccessMessageEnvVarName, defaultInvitationMailMessage)
	OrganizationRejectRequestedAccessTopic   = utils.GetStringEnvOrDefault(organizationRejectRequestedAccessTopicEnvVarName, defaultInvitationMailTopic)

	DefaultWorkspaceName = utils.GetStringEnvOrDefault(defaultWorkspaceNameEnvVarName, defaultWorkspaceNameDefault)

	SSLCertificatesDir = utils.GetStringEnvOrDefault(sslCertificatesDirEnvVarName, "")

	FeatureFlagOrgQuotas        = utils.GetBoolEnvOrDefault(featureFlagOrgQuotasEnvVarName, featureFlagDefaultValue)
	FeatureFlagManageUsers      = utils.GetBoolEnvOrDefault(featureFlagManageUsers, featureFlagDefaultValue)
	FeatureFlagManageUsersRoles = utils.GetBoolEnvOrDefault(featureFlagManageUsersRoles, featureFlagDefaultValue)
	FeatureFlagAccSvcMod        = utils.GetBoolEnvOrDefault(featureFlagAccSvcMod, featureFlagDefaultValue)
	FeatureFlagReqAccess        = utils.GetBoolEnvOrDefault(featureFlagReqAccess, featureFlagDefaultValue)
)
