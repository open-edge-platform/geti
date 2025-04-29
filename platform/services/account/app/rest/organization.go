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

	"account_service/app/common/utils"
	"account_service/app/config"

	"geti.com/account_service_grpc/pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

const (
	grpcRequestTimeout    = 10 * time.Second
	streamBufferSizeBytes = 1024
)

var logger = utils.InitializeLogger()

func HandleOrganizationAddPhoto(w http.ResponseWriter, r *http.Request, pathParams map[string]string) {
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

	orgId := pathParams["id"]
	if orgId == "" {
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

	orgClient := pb.NewOrganizationClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), grpcRequestTimeout)
	defer cancel()

	stream, err := orgClient.AddPhoto(ctx)
	if err != nil {
		logger.Errorf("cannot initialize AddPhoto stream: %v", err)
		http.Error(w, "unexpected error", http.StatusInternalServerError)
		return
	}

	req := pb.OrganizationLogoRequest{
		Request: &pb.OrganizationLogoRequest_UserData{UserData: &pb.OrganizationIdRequest{Id: orgId}},
	}
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

		req := pb.OrganizationLogoRequest{
			Request: &pb.OrganizationLogoRequest_Photo{Photo: buffer[:n]},
		}

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
