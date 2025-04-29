// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package rest

import (
	"bufio"
	"context"
	"io"
	"mime/multipart"
	"net/http"
	"time"

	"account_service/app/config"
	grpcUtils "account_service/app/grpc/utils"

	proto "geti.com/account_service_grpc/pb"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/types/known/emptypb"
)

func HandleUserAddPhoto(w http.ResponseWriter, r *http.Request, pathParams map[string]string) {
	err := r.ParseForm()
	if err != nil {
		logger.Errorf("failed to parse form: %v", err)
		http.Error(w, "failed to parse form", http.StatusBadRequest)
		return
	}

	f, _, err := r.FormFile("file")
	if err != nil {
		logger.Errorf("failed to get key 'file': %v", err)
		http.Error(w, "failed to get key 'file'", http.StatusBadRequest)
		return
	}
	defer func(f multipart.File) {
		err := f.Close()
		if err != nil {
			logger.Errorf("An error ocurred while closing the file from form: %v", err)
		}
	}(f)

	userID := pathParams["user_id"]
	if userID == "" {
		logger.Errorf("failed to get user id from path param")
		http.Error(w, "failed to get user id from path param", http.StatusBadRequest)
		return
	}

	organizationID := pathParams["organization_id"]
	if organizationID == "" {
		logger.Errorf("failed to get org id from path param")
		http.Error(w, "failed to get org id from path param", http.StatusBadRequest)
		return
	}

	conn, err := grpc.Dial(config.GrpcServerAddress, grpc.WithTransportCredentials(insecure.NewCredentials())) //nolint:all (SA1019: deprecated)
	if err != nil {
		logger.Errorf("failed to dial GRPC server: %v", err)
		http.Error(w, "unexpected error", http.StatusInternalServerError)
		return
	}
	defer func(conn *grpc.ClientConn) {
		err := conn.Close()
		if err != nil {
			logger.Errorf("An error ocurred while closing the connection: %v", err)
		}
	}(conn)

	userClient := proto.NewUserClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), grpcRequestTimeout)
	defer cancel()

	stream, err := userClient.AddPhoto(ctx)
	if err != nil {
		logger.Errorf("cannot initialize AddPhoto stream: %v", err)
		http.Error(w, "unexpected error", http.StatusInternalServerError)
		return
	}

	req := proto.UserPhotoRequest{Request: &proto.UserPhotoRequest_UserData{UserData: &proto.UserIdRequest{
		UserId:         userID,
		OrganizationId: organizationID,
	}}}

	err = stream.Send(&req)
	if err != nil {
		logger.Errorf("cannot send stream with user data: %v", err)
		http.Error(w, "unexpected error", http.StatusInternalServerError)
		return
	}

	reader := bufio.NewReader(f)
	buffer := make([]byte, streamBufferSizeBytes)

	for {
		n, err := reader.Read(buffer)
		if err == io.EOF {
			break
		}
		if err != nil {
			logger.Errorf("cannot read chunk to buffer: %v", err)
			http.Error(w, "unexpected error", http.StatusInternalServerError)
			return
		}

		req := proto.UserPhotoRequest{Request: &proto.UserPhotoRequest_Photo{Photo: buffer[:n]}}

		err = stream.Send(&req)
		if err != nil {
			logger.Errorf("cannot send chunk to stream: %v", err)
			http.Error(w, "unexpected error", http.StatusInternalServerError)
			return
		}
	}

	_, err = stream.CloseAndRecv()
	if err != nil {
		logger.Errorf("failed to close stream: %v", err)
		http.Error(w, "unexpected error", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func HandleLogout(w http.ResponseWriter, r *http.Request, pathParams map[string]string) {
	conn, err := grpc.Dial(config.GrpcServerAddress, grpc.WithTransportCredentials(insecure.NewCredentials())) //nolint:all (SA1019: deprecated)
	if err != nil {
		logger.Errorf("failed to dial GRPC server: %v", err)
		http.Error(w, "unexpected error", http.StatusInternalServerError)
		return
	}
	defer func(conn *grpc.ClientConn) {
		err := conn.Close()
		if err != nil {
			logger.Errorf("An error occurred while closing the connection: %v", err)
		}
	}(conn)

	userClient := proto.NewUserClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), grpcRequestTimeout)
	defer cancel()
	ctx = grpcUtils.AddAuthHeadersToContext(ctx, r)

	// Call the Logout gRPC method
	_, err = userClient.Logout(ctx, &emptypb.Empty{})
	if err != nil {
		logger.Errorf("failed to logout: %v", err)
		http.Error(w, "unexpected error", http.StatusInternalServerError)
		return
	}

	// Set the expired cookie
	http.SetCookie(w, &http.Cookie{
		Name:     "geti-cookie",
		Value:    "",
		Path:     "/",
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteStrictMode,
		Expires:  time.Unix(0, 0),
		MaxAge:   -1,
	})

	w.WriteHeader(http.StatusOK)
}
