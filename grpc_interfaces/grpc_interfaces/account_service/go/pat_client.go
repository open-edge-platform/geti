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
