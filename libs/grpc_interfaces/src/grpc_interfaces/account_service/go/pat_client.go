// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package account_service_grpc

import (
	"context"
	"geti.com/account_service_grpc/pb"
	"google.golang.org/grpc"
	"time"
)

type PATclient struct {
	client     pb.PersonalAccessTokenClient
	connection *grpc.ClientConn
}

func InitializePATclient() (PATclient, error) {
	conn, err := InitializeClient("ACCOUNT_SERVICE_ADDRESS", "impt-account-service:5001")
	if err != nil {
		return PATclient{}, err
	}
	return PATclient{
		client:     pb.NewPersonalAccessTokenClient(conn),
		connection: conn,
	}, nil
}

func (c *PATclient) IsInitialized() bool {
	return c.client != nil && c.connection != nil
}

func (c *PATclient) CloseConnection() bool {
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

type AccessTokenData struct {
	Id             string    `json:"id"`
	ExpiresAt      time.Time `json:"expiresAt"`
	OrganizationId string    `json:"organizationId"`
	UserId         string    `json:"userId"`
}

func (c *PATclient) GetPATbyHash(ctx context.Context, hash string) (*AccessTokenData, error) {
	request := &pb.GetByHashRequest{Hash: hash}
	ctx, cancel := context.WithTimeout(ctx, time.Duration(timeoutSeconds)*time.Second)
	defer cancel()

	response, err := c.client.GetByHash(ctx, request)
	if err != nil {
		return nil, err
	}

	token := &AccessTokenData{
		Id:             response.Id,
		ExpiresAt:      TimestampProtoToTime(response.ExpiresAt),
		OrganizationId: response.OrganizationId,
		UserId:         response.UserId,
	}
	return token, nil
}
