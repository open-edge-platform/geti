// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package membership

import (
	"context"
	"errors"

	"account_service/app/common/utils"
	accErr "account_service/app/errors"
	"account_service/app/grpc/common"
	grpcUtils "account_service/app/grpc/utils"
	"account_service/app/models"
	service "account_service/app/services/membership"

	"geti.com/account_service_grpc/pb"

	"github.com/google/uuid"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
	"google.golang.org/protobuf/types/known/timestamppb"
)

var logger = utils.InitializeLogger()

type GRPCServer struct {
	pb.UnimplementedMembershipServer
	Service service.MembershipService
}

func (s *GRPCServer) GetMemberships(ctx context.Context, req *pb.MembershipRequest) (*pb.ListMembershipResponse, error) {
	memberships, totalMatchedCount, err := s.Service.GetMemberships(ctx, req)

	memberships_data := &pb.ListMembershipResponse{}
	for _, membership := range memberships {
		membershipPb, err := membershipToPb(membership)
		if err != nil {
			return nil, err
		}
		memberships_data.Memberships = append(memberships_data.Memberships, membershipPb)
	}

	memberships_data.TotalMatchedCount = int32(totalMatchedCount)

	nextPageFields := common.CalculateNextPage(memberships_data.TotalMatchedCount, req.Skip, req.Limit)
	memberships_data.NextPage = &pb.ListMembershipResponse_NextPage{
		Skip:  nextPageFields.Skip,
		Limit: nextPageFields.Limit,
	}

	if err != nil {
		logger.Errorf("error getting memberships: %v", err)
		return nil, status.Errorf(codes.Internal, "unexpected error")
	}

	return memberships_data, nil
}

func (s *GRPCServer) DeleteMemberships(ctx context.Context, req *pb.DeleteMembershipRequest) (*emptypb.Empty, error) {
	membershipResult, err := s.Service.DeleteMemberships(ctx, req)
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, err.Error())
	}

	return membershipResult, nil
}

func membershipToPb(membership models.MembershipResult) (*pb.MembershipResponse, error) {
	return &pb.MembershipResponse{
		Id:         membership.ID.String(),
		UserId:     membership.UserID.String(),
		FirstName:  membership.FirstName,
		SecondName: membership.SecondName,
		Email:      membership.Email,
		Status:     membership.Status,
		CreatedAt:  timestamppb.New(membership.CreatedAt),
	}, nil
}

func (s *GRPCServer) Modify(ctx context.Context, request *pb.MembershipStatusRequest) (*pb.MembershipStatusResponse, error) {
	logger.Debugf("user status change request - organization %s, user %s, new status: %s",
		request.OrganizationId, request.UserId, request.Payload.Status)

	userID, err := uuid.Parse(request.UserId)
	if err != nil {
		logger.Errorf("error parsing user id: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid user id")
	}

	orgID, err := uuid.Parse(request.OrganizationId)
	if err != nil {
		logger.Errorf("error parsing organization id: %v", err)
		return nil, status.Errorf(codes.InvalidArgument, "invalid organization id")
	}

	newUserStatus, err := s.Service.SetUserStatus(ctx, userID, orgID, request.Payload.Status)
	if err != nil {
		logger.Errorf("error setting memberships: %v", err)
		var conflictErr *accErr.ConflictError
		if errors.As(err, &conflictErr) {
			return nil, status.Errorf(codes.FailedPrecondition, "%v", err)
		} else {
			return nil, status.Errorf(codes.InvalidArgument, "%v", err)
		}

	}

	authTokenData, ok := grpcUtils.GetAuthTokenHeaderData(ctx)
	if ok {
		newUserStatus.CreatedBy = authTokenData.UserID
	}

	response := pb.MembershipStatusResponse{
		Id:             newUserStatus.ID.String(),
		Status:         newUserStatus.Status,
		OrganizationId: newUserStatus.OrganizationID.String(),
		UserId:         newUserStatus.UserID.String(),
		CreatedBy:      newUserStatus.CreatedBy,
		CreatedAt:      timestamppb.New(newUserStatus.CreatedAt),
	}

	return &response, nil

}

func (s *GRPCServer) GetUserMemberships(ctx context.Context, req *pb.UserMembershipRequest) (*pb.ListUserMembershipResponse, error) {
	memberships, totalMatchedCount, err := s.Service.GetUserMemberships(ctx, req)

	memberships_data := &pb.ListUserMembershipResponse{}
	for _, membership := range memberships {
		membershipPb, err := userMembershipToPb(membership)
		if err != nil {
			return nil, err
		}
		memberships_data.Memberships = append(memberships_data.Memberships, membershipPb)
	}

	memberships_data.TotalMatchedCount = int32(totalMatchedCount)

	nextPageFields := common.CalculateNextPage(memberships_data.TotalMatchedCount, req.Skip, req.Limit)
	memberships_data.NextPage = &pb.ListUserMembershipResponse_NextPage{
		Skip:  nextPageFields.Skip,
		Limit: nextPageFields.Limit,
	}

	if err != nil {
		logger.Errorf("error getting memberships: %v", err)
		return nil, status.Errorf(codes.Internal, "unexpected error")
	}

	return memberships_data, nil
}

func userMembershipToPb(membership models.UserMembershipResult) (*pb.UserMembershipResponse, error) {
	return &pb.UserMembershipResponse{
		Id:               membership.ID.String(),
		OrganizationId:   membership.OrganizationID.String(),
		OrganizationName: membership.OrganizationName,
		Status:           membership.Status,
		CreatedAt:        timestamppb.New(membership.CreatedAt),
	}, nil
}
