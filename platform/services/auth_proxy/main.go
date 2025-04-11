// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package main

import (
	"auth_proxy/app/http"
	"auth_proxy/app/jwk"
	"auth_proxy/app/request_processor"
	"auth_proxy/app/utils"
	"fmt"
	"net"

	"google.golang.org/grpc"

	extProcPb "github.com/envoyproxy/go-control-plane/envoy/service/ext_proc/v3"
)

var logger = utils.InitializeBasicLogger()

func CreateTcpListener(address string) net.Listener {
	tcpListener, err := net.Listen("tcp", address)
	if err != nil {
		logger.Fatal("failed to listen: %v", err)
	}
	return tcpListener
}

func registerBackgroundTasks() {
	logger.Debug("Registering background tasks")

	go jwk.ScheduleJWKSUpdate()
}

func main() {
	registerBackgroundTasks()

	httpPort := utils.GetEnv("HTTP_SERVER_PORT", "7002")
	go http.StartServer(httpPort)

	grpcPort := utils.GetEnv("GRPC_SERVER_PORT", "7001")
	grpcAddress := fmt.Sprintf(":%v", grpcPort)
	tcpListener := CreateTcpListener(grpcAddress)
	grpcServer := grpc.NewServer()
	externalProcessor := &request_processor.ExtProcServer{}
	err := externalProcessor.Init()
	if err != nil {
		logger.Fatalf("failed to initialize external processing server: %v", err) //calls os.Exit(1)
	}
	extProcPb.RegisterExternalProcessorServer(grpcServer, externalProcessor)
	logger.Infof("Starting gRPC server on address %s", grpcAddress)
	err = grpcServer.Serve(tcpListener)
	if err != nil {
		logger.Fatalf("failed to serve gRPC: %v", err)
	}
}
