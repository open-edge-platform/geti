// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package organization

//import (
//	"context"
//	"errors"
//	"testing"
//
//	"account_service/app/grpc"
//	"account_service/app/models"
//
//	"github.com/golang/mock/gomock"
//	"github.com/stretchr/testify/assert"
//	"gorm.io/gorm"
//)
//
//func TestGetById(t *testing.T) {
//	ctrl := gomock.NewController(t)
//	dbMock := grpc.NewMockIGormDB(ctrl)
//	srv := GRPCServer{DB: dbMock}
//
//	ctx := context.Background()
//
//	idReq := OrganizationIdRequest{
//		Id: "fake-id",
//	}
//
//	fakeName := "some-name"
//
//	dbMock.EXPECT().First(gomock.Any(), gomock.Any()).DoAndReturn(func(dest interface{}, conds ...interface{}) (tx *gorm.DB) {
//		org, ok := dest.(*models.Organization)
//		if !ok {
//			t.Fatalf("error converting")
//		}
//		org.Name = fakeName
//		return &gorm.DB{}
//
//	})
//
//	pbOrg, err := srv.GetById(ctx, &idReq)
//	if err != nil {
//		t.Fatalf("%v", err)
//	}
//
//	assert.Equal(t, pbOrg.Name, fakeName)
//}
//
//func TestGetByIdNotFound(t *testing.T) {
//	ctrl := gomock.NewController(t)
//	dbMock := grpc.NewMockIGormDB(ctrl)
//	srv := GRPCServer{DB: dbMock}
//
//	ctx := context.Background()
//
//	idReq := OrganizationIdRequest{
//		Id: "fake-id",
//	}
//
//	dbMock.EXPECT().First(gomock.Any(), gomock.Any()).DoAndReturn(func(dest interface{}, conds ...interface{}) (tx *gorm.DB) {
//		return &gorm.DB{Error: gorm.ErrRecordNotFound}
//	})
//	_, err := srv.GetById(ctx, &idReq)
//	assert.Error(t, err)
//}
//
//func TestGetByIdUnknownError(t *testing.T) {
//	ctrl := gomock.NewController(t)
//	dbMock := grpc.NewMockIGormDB(ctrl)
//	srv := GRPCServer{DB: dbMock}
//
//	ctx := context.Background()
//
//	idReq := OrganizationIdRequest{
//		Id: "fake-id",
//	}
//
//	dbMock.EXPECT().First(gomock.Any(), gomock.Any()).DoAndReturn(func(dest interface{}, conds ...interface{}) (tx *gorm.DB) {
//		return &gorm.DB{Error: errors.New("some error")}
//	})
//	_, err := srv.GetById(ctx, &idReq)
//	assert.Error(t, err)
//}
