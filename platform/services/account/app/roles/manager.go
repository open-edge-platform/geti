// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package roles

import (
	"context"
	"io"

	"account_service/app/config"

	v1 "github.com/authzed/authzed-go/proto/authzed/api/v1"
	"github.com/authzed/authzed-go/v1"
	"github.com/authzed/grpcutil"
	"google.golang.org/grpc"
	grpcCodes "google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	grpcStatus "google.golang.org/grpc/status"
)

type RolesManager struct {
	client *authzed.Client
}

type IRolesManager interface {
	WriteSchema() error
	WriteRelationship(relation string, subject *v1.SubjectReference, resource *v1.ObjectReference, operation v1.RelationshipUpdate_Operation) error
	GetRelationships(filter *v1.RelationshipFilter) ([]*v1.Relationship, error)
	GetOrganizationRelationships(orgID string, relation string) ([]*v1.Relationship, error)
	GetUserAllRelationships(userID string) ([]*v1.Relationship, error)
	CheckRelationshipToDelete(relationship *v1.Relationship, orgID string) (bool, error)
	ChangeUserRelation(resourceType string, resourceID string, relations []string, userID string, operation v1.RelationshipUpdate_Operation) error
}

func NewRolesManager(spiceDBAddress string, spiceDBToken string) (*RolesManager, error) {
	certDir := config.SSLCertificatesDir

	var client *authzed.Client
	var err error

	if certDir != "" {
		option, errl := grpcutil.WithCustomCerts(grpcutil.SkipVerifyCA,
			certDir+"/ca.crt")

		if errl != nil {
			return nil, errl
		}

		client, err = authzed.NewClient(
			spiceDBAddress,
			grpc.WithTransportCredentials(insecure.NewCredentials()),
			grpcutil.WithBearerToken(spiceDBToken),
			option,
		)

	} else {
		client, err = authzed.NewClient(
			spiceDBAddress,
			grpc.WithTransportCredentials(insecure.NewCredentials()),
			grpcutil.WithInsecureBearerToken(spiceDBToken),
		)
	}

	if err != nil {
		return nil, err
	}

	return &RolesManager{client: client}, nil
}

func (m *RolesManager) WriteSchema() error {
	req := v1.WriteSchemaRequest{Schema: spicedbSchema}
	_, err := m.client.WriteSchema(context.Background(), &req)
	if err != nil {
		return err
	}
	return nil
}

func (m *RolesManager) WriteRelationship(relation string, subject *v1.SubjectReference, resource *v1.ObjectReference, operation v1.RelationshipUpdate_Operation) error {
	relationshipUpdate := v1.RelationshipUpdate{
		Operation: operation,
		Relationship: &v1.Relationship{
			Resource: resource,
			Relation: relation,
			Subject:  subject,
		},
	}

	req := v1.WriteRelationshipsRequest{
		Updates: []*v1.RelationshipUpdate{&relationshipUpdate},
	}

	ctx := context.Background()
	_, err := m.client.WriteRelationships(ctx, &req)
	if err != nil {
		errStatus, ok := grpcStatus.FromError(err)
		if ok {
			grpcStatusCode := errStatus.Code()
			grpcStatusMessage := errStatus.Message()
			if grpcStatusCode == grpcCodes.FailedPrecondition {
				return NewInvalidRoleError(grpcStatusMessage)
			} else if grpcStatusCode == grpcCodes.AlreadyExists {
				return NewRoleAlreadyExistsError(grpcStatusMessage, &relationshipUpdate)
			}
		}
		return err
	}
	return nil
}

func (m *RolesManager) GetRelationships(filter *v1.RelationshipFilter) ([]*v1.Relationship, error) {
	var relationships []*v1.Relationship

	fullyConsistentConsistency := &v1.Consistency_FullyConsistent{FullyConsistent: true}
	readReq := v1.ReadRelationshipsRequest{
		Consistency:        &v1.Consistency{Requirement: fullyConsistentConsistency},
		RelationshipFilter: filter,
	}
	ctx := context.Background()
	stream, err := m.client.ReadRelationships(ctx, &readReq)
	if err != nil {
		return relationships, err
	}

	for {
		resp, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			return relationships, err
		}

		relationship := resp.GetRelationship()
		relationships = append(relationships, relationship)

	}

	return relationships, nil
}
