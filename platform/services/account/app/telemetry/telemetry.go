// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package telemetry

import (
	"context"
	"time"

	"google.golang.org/grpc"

	"account_service/app/common/utils"
	"account_service/app/config"
	"account_service/app/grpc/organization"
	"account_service/app/grpc/user"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc"
	"go.opentelemetry.io/otel/metric"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"gorm.io/gorm"
)

const (
	StatusACT        = "ACT"
	StatusRGS        = "RGS"
	UserTypeInternal = "internal"
	UserTypeExternal = "external"
)

var (
	logger = utils.InitializeLogger()
	meter  metric.Meter

	organizationsGauge metric.Int64ObservableGauge
	activeUsersGauge   metric.Int64ObservableGauge
	invitedUsersGauge  metric.Int64ObservableGauge
)

func InitMeter() {
	logger.Info("Initializing OpenTelemetry meter")
	ctx := context.Background()
	exporter, err := otlpmetricgrpc.New(ctx,
		otlpmetricgrpc.WithInsecure(),
		otlpmetricgrpc.WithEndpoint(config.OtelMetricsReceiver),
		otlpmetricgrpc.WithDialOption(grpc.WithBlock()), //nolint:all (SA1019: deprecated)
	)
	if err != nil {
		logger.Fatalf("Failed to create the collector exporter: %v", err)
	}
	logger.Infof("Created OTLP metric exporter with endpoint: %s", config.OtelMetricsReceiver)

	provider := sdkmetric.NewMeterProvider(
		sdkmetric.WithReader(sdkmetric.NewPeriodicReader(exporter, sdkmetric.WithInterval(8*time.Hour))),
	)
	otel.SetMeterProvider(provider)
	meter = otel.Meter(config.OtelServiceName)
	logger.Infof("Meter initialized with service name: %s", config.OtelServiceName)
}

func InitGauges() {
	logger.Info("Initializing metric gauges")
	var err error
	organizationsGauge, err = meter.Int64ObservableGauge("organizations_number")
	if err != nil {
		logger.Fatalf("Failed to create organizations gauge: %v", err)
	}
	logger.Info("Created organizations_number gauge")

	activeUsersGauge, err = meter.Int64ObservableGauge("number_of_active_users")
	if err != nil {
		logger.Fatalf("Failed to create active users gauge: %v", err)
	}
	logger.Info("Created number_of_active_users gauge")

	invitedUsersGauge, err = meter.Int64ObservableGauge("number_of_invited_users")
	if err != nil {
		logger.Fatalf("Failed to create invited users gauge: %v", err)
	}
	logger.Info("Created number_of_invited_users gauge")
}

func RegisterMetricsCallback(db *gorm.DB) {
	if !config.OtelEnableMetrics {
		logger.Info("Metrics reporting is disabled")
		return
	}
	logger.Info("Registering metrics callback")

	_, err := meter.RegisterCallback(
		func(ctx context.Context, result metric.Observer) error {
			logger.Info("Metrics callback triggered")

			statuses, err := organization.CountOrganizationStatuses(db)
			if err != nil {
				logger.Errorf("Failed to retrieve organization statuses: %v", err)
			} else {
				logger.Infof("Retrieved organization statuses: %+v", statuses)
				for status, count := range statuses {
					result.ObserveInt64(organizationsGauge, count, metric.WithAttributes(attribute.String("status", status)))
					logger.Infof("Observed organization count: status=%s, count=%d", status, count)
				}
			}

			activeUsers, err := user.CountUsersByStatus(db, StatusACT)
			if err != nil {
				logger.Errorf("Failed to retrieve active users: %v", err)
			} else {
				logger.Infof("Retrieved active users: %+v", activeUsers)
				result.ObserveInt64(activeUsersGauge, activeUsers[UserTypeInternal], metric.WithAttributes(attribute.String("type", UserTypeInternal)))
				result.ObserveInt64(activeUsersGauge, activeUsers[UserTypeExternal], metric.WithAttributes(attribute.String("type", UserTypeExternal)))
				logger.Infof("Observed active users: internal=%d, external=%d", activeUsers[UserTypeInternal], activeUsers[UserTypeExternal])
			}

			invitedUsers, err := user.CountUsersByStatus(db, StatusRGS)
			if err != nil {
				logger.Errorf("Failed to retrieve invited users: %v", err)
			} else {
				logger.Infof("Retrieved invited users: %+v", invitedUsers)
				result.ObserveInt64(invitedUsersGauge, invitedUsers[UserTypeInternal], metric.WithAttributes(attribute.String("type", UserTypeInternal)))
				result.ObserveInt64(invitedUsersGauge, invitedUsers[UserTypeExternal], metric.WithAttributes(attribute.String("type", UserTypeExternal)))
				logger.Infof("Observed invited users: internal=%d, external=%d", invitedUsers[UserTypeInternal], invitedUsers[UserTypeExternal])
			}

			logger.Info("Metrics callback completed")
			return nil
		},
		organizationsGauge,
		activeUsersGauge,
		invitedUsersGauge,
	)

	if err != nil {
		logger.Fatalf("Failed to register callback for metrics: %v", err)
	}
	logger.Info("Metrics callback registered successfully")
}
