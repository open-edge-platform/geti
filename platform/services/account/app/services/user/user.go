// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package user

import (
	"account_service/app/models"
	"account_service/app/repository"
	"context"

	proto "geti.com/account_service_grpc/pb"
)

type UserService interface {
	GetUsers(ctx context.Context, req *proto.GetUsersRequest) ([]models.User, int64, error)
}

type userService struct {
	repo repository.UserRepository
}

func NewuserService(repo repository.UserRepository) UserService {
	return &userService{repo: repo}
}

func (s *userService) GetUsers(ctx context.Context, req *proto.GetUsersRequest) ([]models.User, int64, error) {
	dataQuery := repository.UserQuery{FirstName: req.FirstName, SecondName: req.SecondName, Email: req.Email, ExternalId: req.ExternalId, Country: req.Country, LastSuccessfulLogin: req.LastSuccessfulLogin, CurrentSuccessfulLogin: req.CurrentSuccessfulLogin, CreatedFrom: req.CreatedAtFrom, ModifiedFrom: req.ModifiedAtFrom, ModifiedTo: req.ModifiedAtTo, UserConsentFrom: req.UserConsentFrom, UserConsentTo: req.UserConsentTo, Name: req.Name, SortBy: req.SortBy, SortDirection: req.SortDirection, Skip: req.Skip, Limit: req.Limit}
	users, totalMatchedCount, err := s.repo.FindUsers(ctx, &dataQuery)
	if err != nil {
		return nil, 0, err
	}

	return users, totalMatchedCount, nil
}
