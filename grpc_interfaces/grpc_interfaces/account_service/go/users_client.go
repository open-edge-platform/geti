// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package account_service_grpc

import (
	"context"
	"geti.com/account_service_grpc/pb"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/timestamppb"
	"time"
)

type UsersClient struct {
	client     pb.UserClient
	connection *grpc.ClientConn
}

func InitializeUsersClient() (UsersClient, error) {
	conn, err := InitializeClient("ACCOUNT_SERVICE_ADDRESS", "impt-account-service:5001")
	if err != nil {
		return UsersClient{}, err
	}
	return UsersClient{
		client:     pb.NewUserClient(conn),
		connection: conn,
	}, nil
}

func (c *UsersClient) IsInitialized() bool {
	return c.client != nil && c.connection != nil
}

func (c *UsersClient) CloseConnection() bool {
	if !c.IsInitialized() {
		return false
	}
	err := CloseClientConnection(c.connection)
	if err != nil {
		return false
	}
	c.client = nil
	c.connection = nil
	return true
}

type User struct {
	UserId             string                 `json:"id"`
	FirstName          string                 `json:"firstName"`
	SecondName         string                 `json:"secondName"`
	Email              string                 `json:"email"`
	ExternalId         string                 `json:"externalId"`
	Country            string                 `json:"country"`
	Status             string                 `json:"status"`
	OrganizationId     string                 `json:"organizationId"`
	OrganizationStatus string                 `json:"organizationStatus"`
	PreviousLoginTime  time.Time              `json:"lastSuccessfulLogin"`
	CurrentLoginTime   time.Time              `json:"currentSuccessfulLogin"`
	LastLogoutDate     time.Time              `json:"lastLogoutDate"`
	ModifiedBy         string                 `json:"modifiedBy"`
	TelemetryConsent   *string                `json:"telemetryConsent"`
	TelemetryConsentAt *timestamppb.Timestamp `json:"telemetryConsentAt"`
	UserConsent        *string                `json:"userConsent"`
	UserConsentAt      *timestamppb.Timestamp `json:"userConsentAt"`
}

func (c *UsersClient) GetUserByExternalId(ctx context.Context, externalId string) (*User, error) {
	request := &pb.UserExtIdRequest{Id: externalId}
	// Configure context with timeout
	ctx, cancel := context.WithTimeout(ctx, time.Duration(timeoutSeconds)*time.Second)
	defer cancel()

	response, err := c.client.GetByExternalId(ctx, request)
	if err != nil {
		return nil, err
	}
	user := &User{
		UserId:             response.Id,
		FirstName:          response.FirstName,
		SecondName:         response.SecondName,
		Email:              response.Email,
		ExternalId:         response.ExternalId,
		Country:            response.Country,
		Status:             response.Status,
		OrganizationId:     response.OrganizationId,
		OrganizationStatus: response.OrganizationStatus,
		PreviousLoginTime:  TimestampProtoToTime(response.LastSuccessfulLogin),
		CurrentLoginTime:   TimestampProtoToTime(response.CurrentSuccessfulLogin),
		LastLogoutDate:     TimestampProtoToTime(response.LastLogoutDate),
		ModifiedBy:         response.ModifiedBy,
		TelemetryConsent:   response.TelemetryConsent,
		TelemetryConsentAt: response.TelemetryConsentAt,
		UserConsent:        response.UserConsent,
		UserConsentAt:      response.UserConsentAt,
	}
	return user, nil
}

func (c *UsersClient) UpdateUserData(ctx context.Context, data *User) error {
	// Configure context with timeout
	ctx, cancel := context.WithTimeout(ctx, time.Duration(timeoutSeconds)*time.Second)
	defer cancel()

	newData := &pb.UserData{
		Id:                     data.UserId,
		FirstName:              data.FirstName,
		SecondName:             data.SecondName,
		Email:                  data.Email,
		ExternalId:             data.ExternalId,
		Country:                data.Country,
		Status:                 data.Status,
		OrganizationId:         data.OrganizationId,
		OrganizationStatus:     data.OrganizationStatus,
		LastSuccessfulLogin:    TimeToTimestampProto(data.PreviousLoginTime),
		CurrentSuccessfulLogin: TimeToTimestampProto(data.CurrentLoginTime),
		ModifiedBy:             data.ModifiedBy,
		TelemetryConsent:       data.TelemetryConsent,
		TelemetryConsentAt:     data.TelemetryConsentAt,
		UserConsent:            data.UserConsent,
		UserConsentAt:          data.UserConsentAt,
	}
	_, err := c.client.Modify(ctx, newData)
	if err != nil {
		return err
	}
	return nil
}
